"""Org user search / create API smoke tests."""

from __future__ import annotations

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
        assert all(
            "adm" in u["username"].lower()
            or (u.get("nickname") or "").lower().find("adm") >= 0
            for u in hits
        )

        empty = await client.get(
            "/api/v1/users",
            headers=headers,
            params={"q": "no-such-user-zzzz"},
        )
        assert empty.status_code == 200
        assert empty.json()["data"]["items"] == []


@pytest.mark.asyncio
async def test_admin_create_org_user() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    username = f"u_{uuid.uuid4().hex[:10]}"
    password = "User@123456"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        created = await client.post(
            "/api/v1/users",
            headers=headers,
            json={
                "username": username,
                "password": password,
                "nickname": "Demo User",
            },
        )
        assert created.status_code == 200, created.text
        data = created.json()["data"]
        assert data["username"] == username
        assert data["status"] == "ACTIVE"

        conflict = await client.post(
            "/api/v1/users",
            headers=headers,
            json={"username": username, "password": password},
        )
        assert conflict.status_code == 409
        assert conflict.json()["code"] == "USER_NAME_CONFLICT"

        login_new = await client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        assert login_new.status_code == 200, login_new.text
        assert "USER" in login_new.json()["data"]["user"]["roles"]

        audits = await client.get(
            "/api/v1/audit-logs",
            headers=headers,
            params={"action": "user.create", "page_size": 50},
        )
        assert audits.status_code == 200
        assert any(
            i["action"] == "user.create" and i["resource_id"] == data["id"]
            for i in audits.json()["data"]["items"]
        )