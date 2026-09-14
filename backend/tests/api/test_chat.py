"""Conversation + RAG SSE chat smoke tests."""

from __future__ import annotations

import asyncio
import io
import json
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


async def _wait_job(
    client: AsyncClient,
    headers: dict[str, str],
    document_id: str,
    *,
    timeout: float = 15.0,
) -> dict:
    deadline = asyncio.get_event_loop().time() + timeout
    last = None
    while asyncio.get_event_loop().time() < deadline:
        jobs = await client.get(
            f"/api/v1/documents/{document_id}/jobs",
            headers=headers,
        )
        assert jobs.status_code == 200
        items = jobs.json()["data"]["items"]
        last = items[0]
        if last["status"] in {"SUCCESS", "FAILED"}:
            return last
        await asyncio.sleep(0.2)
    raise AssertionError(f"job timeout last={last}")


def _parse_sse(raw: str) -> list[dict]:
    events: list[dict] = []
    for block in raw.split("\n\n"):
        line = block.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload:
            events.append(json.loads(payload))
    return events


@pytest.mark.asyncio
async def test_rag_chat_stream_with_citation() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        kb = await client.post(
            "/api/v1/knowledge-bases",
            headers=headers,
            json={
                "name": f"ChatKB-{uuid.uuid4().hex[:8]}",
                "visibility": "PRIVATE",
            },
        )
        assert kb.status_code == 200, kb.text
        kb_id = kb.json()["data"]["id"]

        content = (
            "# 员工手册\n\n"
            "年假制度：正式员工入职满一年可享有带薪年假 5 天。\n"
            "请假需提前三天在系统中提交申请。\n"
        ).encode()
        upload = await client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            headers=headers,
            files={"file": ("handbook.md", io.BytesIO(content), "text/markdown")},
        )
        assert upload.status_code == 200, upload.text
        document_id = upload.json()["data"]["id"]
        job = await _wait_job(client, headers, document_id)
        assert job["status"] == "SUCCESS", job

        conv = await client.post(
            "/api/v1/conversations",
            headers=headers,
            json={"title": "年假咨询", "kb_ids": [kb_id]},
        )
        assert conv.status_code == 200, conv.text
        conversation_id = conv.json()["data"]["id"]

        stream = await client.post(
            "/api/v1/chat/stream",
            headers={**headers, "Accept": "text/event-stream"},
            json={
                "conversation_id": conversation_id,
                "question": "年假有几天？",
                "kb_ids": [kb_id],
            },
        )
        assert stream.status_code == 200, stream.text
        assert "text/event-stream" in stream.headers.get("content-type", "")
        events = _parse_sse(stream.text)
        names = [e["event"] for e in events]
        assert names[0] == "start"
        assert "citation" in names
        assert "text" in names
        assert names[-1] == "done"
        assert all(e["seq"] == i for i, e in enumerate(events, start=1))

        cite_event = next(e for e in events if e["event"] == "citation")
        assert cite_event["data"]["citations"]
        assert cite_event["data"]["citations"][0]["document_id"] == document_id

        messages = await client.get(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=headers,
        )
        assert messages.status_code == 200
        items = messages.json()["data"]["items"]
        assert len(items) >= 2
        assistant = next(m for m in items if m["role"] == "ASSISTANT")
        assert assistant["status"] == "COMPLETED"
        assert assistant["content"]
        assert assistant["citations"]


@pytest.mark.asyncio
async def test_rag_refuse_when_kb_empty() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        kb = await client.post(
            "/api/v1/knowledge-bases",
            headers=headers,
            json={
                "name": f"EmptyKB-{uuid.uuid4().hex[:8]}",
                "visibility": "PRIVATE",
            },
        )
        kb_id = kb.json()["data"]["id"]
        conv = await client.post(
            "/api/v1/conversations",
            headers=headers,
            json={"kb_ids": [kb_id]},
        )
        conversation_id = conv.json()["data"]["id"]

        stream = await client.post(
            "/api/v1/chat/stream",
            headers=headers,
            json={
                "conversation_id": conversation_id,
                "question": "随便问点什么",
                "kb_ids": [kb_id],
            },
        )
        assert stream.status_code == 200
        events = _parse_sse(stream.text)
        assert events[0]["event"] == "start"
        assert events[-1]["event"] == "done"
        text_parts = [
            e["data"]["content"] for e in events if e["event"] == "text"
        ]
        full = "".join(text_parts)
        assert "未找到可靠依据" in full
