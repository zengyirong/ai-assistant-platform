"""Document / Job API smoke tests against real MySQL (uses .env)."""

from __future__ import annotations

import asyncio
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


async def _create_kb(client: AsyncClient, headers: dict[str, str]) -> str:
    create = await client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={
            "name": f"DocKB-{uuid.uuid4().hex[:8]}",
            "visibility": "PRIVATE",
        },
    )
    assert create.status_code == 200, create.text
    return create.json()["data"]["id"]


async def _wait_job(
    client: AsyncClient,
    headers: dict[str, str],
    document_id: str,
    *,
    timeout: float = 10.0,
) -> dict:
    deadline = asyncio.get_event_loop().time() + timeout
    last = None
    while asyncio.get_event_loop().time() < deadline:
        jobs = await client.get(
            f"/api/v1/documents/{document_id}/jobs",
            headers=headers,
        )
        assert jobs.status_code == 200, jobs.text
        items = jobs.json()["data"]["items"]
        assert items
        last = items[0]
        if last["status"] in {"SUCCESS", "FAILED", "CANCELLED"}:
            return last
        await asyncio.sleep(0.2)
    raise AssertionError(f"job timeout, last={last}")


@pytest.mark.asyncio
async def test_document_upload_pipeline_and_dedupe() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        kb_id = await _create_kb(client, headers)

        content = b"# Hello\n\nPhase1 document pipeline smoke test.\n" * 20
        upload = await client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            headers=headers,
            files={"file": ("handbook.md", io.BytesIO(content), "text/markdown")},
        )
        assert upload.status_code == 200, upload.text
        doc = upload.json()["data"]
        document_id = doc["id"]
        assert doc["status"] == "UPLOADED"
        assert doc["job_id"]
        assert doc["file_type"] == "md"

        job = await _wait_job(client, headers, document_id)
        assert job["status"] == "SUCCESS", job

        detail = await client.get(
            f"/api/v1/documents/{document_id}",
            headers=headers,
        )
        assert detail.status_code == 200
        assert detail.json()["data"]["status"] == "READY"

        from app.ai.vectorstore import get_vector_store

        store = get_vector_store()
        counted = await store.count_by_document(document_id)
        assert counted >= 1

        listed = await client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            headers=headers,
        )
        assert listed.status_code == 200
        assert any(i["id"] == document_id for i in listed.json()["data"]["items"])

        dup = await client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            headers=headers,
            files={"file": ("handbook-copy.md", io.BytesIO(content), "text/markdown")},
        )
        assert dup.status_code == 409
        assert dup.json()["code"] == "DOCUMENT_DUPLICATED"

        deleted = await client.delete(
            f"/api/v1/documents/{document_id}",
            headers=headers,
        )
        assert deleted.status_code == 200

        gone = await client.get(
            f"/api/v1/documents/{document_id}",
            headers=headers,
        )
        assert gone.status_code == 404


@pytest.mark.asyncio
async def test_unsupported_binary_fails_job_and_retry() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        kb_id = await _create_kb(client, headers)

        upload = await client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            headers=headers,
            files={
                "file": (
                    "stub.pdf",
                    io.BytesIO(b"%PDF-1.4 fake"),
                    "application/pdf",
                )
            },
        )
        assert upload.status_code == 200, upload.text
        document_id = upload.json()["data"]["id"]

        job = await _wait_job(client, headers, document_id)
        assert job["status"] == "FAILED"
        assert job["error_code"] == "DOCUMENT_PARSE_FAILED"

        detail = await client.get(
            f"/api/v1/documents/{document_id}",
            headers=headers,
        )
        assert detail.json()["data"]["status"] == "FAILED"

        # Replace storage content path isn't changed; retry still fails for pdf —
        # assert retry creates a new FAILED job.
        retry = await client.post(
            f"/api/v1/documents/{document_id}/retry",
            headers=headers,
        )
        assert retry.status_code == 200, retry.text
        assert retry.json()["data"]["status"] == "PENDING"

        job2 = await _wait_job(client, headers, document_id)
        assert job2["status"] == "FAILED"
        assert job2["retry_count"] >= 1
