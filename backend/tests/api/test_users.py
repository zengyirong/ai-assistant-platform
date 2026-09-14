"""Org user search API smoke tests."""

from __future__ import annotations

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
async def test_list_org_users_and_search() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        listed = await client.get("/api/v1/users", headers=headers)
        assert listed.status_code == 200, listed.text
        body = listed.json()
        assert body["code"] == "OK"
        items = body["data"]["items"]
        assert any(u["username"] == "admin" for u in items)

        searched = await client.get(
            "/api/v1/users",
            headers=headers,
            params={"q": "adm"},
        )
        assert searched.status_code == 200
        hits = searched.json()["data"]["items"]
        assert hits
        assert all("adm" in u["username"].lower() or (u.get("nickname") or "").lower().find("adm") >= 0 for u in hits)

        empty = await client.get(
            "/api/v1/users",
            headers=headers,
            params={"q": "no-such-user-zzzz"},
        )
        assert empty.status_code == 200
        assert empty.json()["data"]["items"] == []
