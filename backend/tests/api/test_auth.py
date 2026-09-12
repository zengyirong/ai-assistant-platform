"""Auth API smoke tests against real MySQL (uses .env)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.asyncio
async def test_login_me_logout() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        bad = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert bad.status_code == 401
        assert bad.json()["code"] == "AUTH_UNAUTHORIZED"

        login = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "Admin@123456"},
        )
        assert login.status_code == 200
        body = login.json()
        assert body["code"] == "OK"
        token = body["data"]["access_token"]
        assert body["data"]["user"]["username"] == "admin"
        assert "ADMIN" in body["data"]["user"]["roles"]

        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 200
        me_data = me.json()["data"]
        assert me_data["username"] == "admin"
        assert "knowledge:list" in me_data["permissions"]

        logout = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout.status_code == 200
        assert logout.json()["code"] == "OK"
