"""Knowledge base API smoke tests against real MySQL (uses .env)."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app

SPACE_ID = "55555555-5555-5555-5555-555555555555"


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
async def test_knowledge_base_crud_members_rag_config() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        create = await client.post(
            "/api/v1/knowledge-bases",
            headers=headers,
            json={
                "name": f"KB-{uuid.uuid4().hex[:8]}",
                "description": "phase1 smoke",
                "visibility": "PRIVATE",
            },
        )
        assert create.status_code == 200, create.text
        kb = create.json()["data"]
        kb_id = kb["id"]
        assert kb["visibility"] == "PRIVATE"
        assert kb["status"] == "ACTIVE"

        listed = await client.get("/api/v1/knowledge-bases", headers=headers)
        assert listed.status_code == 200
        assert any(item["id"] == kb_id for item in listed.json()["data"]["items"])

        detail = await client.get(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["data"]["id"] == kb_id

        updated = await client.put(
            f"/api/v1/knowledge-bases/{kb_id}",
            headers=headers,
            json={
                "name": "Updated KB",
                "visibility": "SPACE",
                "space_id": SPACE_ID,
            },
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["data"]["visibility"] == "SPACE"
        assert updated.json()["data"]["space_id"] == SPACE_ID

        members = await client.get(
            f"/api/v1/knowledge-bases/{kb_id}/members",
            headers=headers,
        )
        assert members.status_code == 200
        items = members.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["role"] == "OWNER"

        rag = await client.get(
            f"/api/v1/knowledge-bases/{kb_id}/rag-config",
            headers=headers,
        )
        assert rag.status_code == 200
        assert rag.json()["data"]["chunk_size"] == 800

        rag_put = await client.put(
            f"/api/v1/knowledge-bases/{kb_id}/rag-config",
            headers=headers,
            json={"chunk_size": 1000, "top_k": 8, "temperature": 0.3},
        )
        assert rag_put.status_code == 200, rag_put.text
        assert rag_put.json()["data"]["chunk_size"] == 1000
        assert rag_put.json()["data"]["top_k"] == 8

        deleted = await client.delete(
            f"/api/v1/knowledge-bases/{kb_id}",
            headers=headers,
        )
        assert deleted.status_code == 200

        gone = await client.get(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)
        assert gone.status_code == 404
        assert gone.json()["code"] == "KB_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_space_kb_requires_space_id() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        bad = await client.post(
            "/api/v1/knowledge-bases",
            headers=headers,
            json={"name": "bad-space-kb", "visibility": "SPACE"},
        )
        assert bad.status_code == 400
        assert bad.json()["code"] == "VALIDATION_ERROR"
