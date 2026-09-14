"""Audit log API tests."""

from __future__ import annotations

import io
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _login(client: AsyncClient) -> str:
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin@123456"},
    )
    assert login.status_code == 200, login.text
    return login.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_audit_logs_after_login_and_kb_member() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        logs = await client.get("/api/v1/audit-logs", headers=headers)
        assert logs.status_code == 200, logs.text
        body = logs.json()
        assert body["code"] == "OK"
        assert any(item["action"] == "auth.login" for item in body["data"]["items"])

        create = await client.post(
            "/api/v1/knowledge-bases",
            headers=headers,
            json={
                "name": f"AuditKB-{uuid.uuid4().hex[:8]}",
                "visibility": "PRIVATE",
            },
        )
        assert create.status_code == 200, create.text
        kb_id = create.json()["data"]["id"]

        me = await client.get("/api/v1/auth/me", headers=headers)
        admin_id = me.json()["data"]["id"]

        # upsert self as VIEWER then back — still produces audit
        add = await client.post(
            f"/api/v1/knowledge-bases/{kb_id}/members",
            headers=headers,
            json={"user_id": admin_id, "role": "OWNER"},
        )
        assert add.status_code == 200, add.text

        filtered = await client.get(
            "/api/v1/audit-logs",
            headers=headers,
            params={"action": "kb.member.upsert", "page_size": 50},
        )
        assert filtered.status_code == 200
        items = filtered.json()["data"]["items"]
        assert any(
            i["action"] == "kb.member.upsert" and i["resource_id"] == kb_id
            for i in items
        )

        # cleanup
        await client.delete(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)


@pytest.mark.asyncio
async def test_audit_document_upload() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        create = await client.post(
            "/api/v1/knowledge-bases",
            headers=headers,
            json={
                "name": f"AuditDoc-{uuid.uuid4().hex[:8]}",
                "visibility": "PRIVATE",
            },
        )
        assert create.status_code == 200, create.text
        kb_id = create.json()["data"]["id"]

        content = b"# audit doc\n\nhello audit.\n"
        upload = await client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            headers=headers,
            files={"file": ("audit.md", io.BytesIO(content), "text/markdown")},
        )
        assert upload.status_code == 200, upload.text
        doc_id = upload.json()["data"]["id"]

        logs = await client.get(
            "/api/v1/audit-logs",
            headers=headers,
            params={"action": "document.upload", "page_size": 50},
        )
        assert logs.status_code == 200
        assert any(
            i["resource_id"] == doc_id for i in logs.json()["data"]["items"]
        )

        await client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
        await client.delete(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)
