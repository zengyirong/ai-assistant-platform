"""RBAC / system admin API smoke tests (M7)."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _login(client: AsyncClient, username: str, password: str) -> str:
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_menu_all_admin_vs_user() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin_token = await _login(client, "admin", "Admin@123456")
        admin_menus = await client.get(
            "/api/v1/menu/all",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_menus.status_code == 200, admin_menus.text
        admin_tree = admin_menus.json()["data"]
        assert isinstance(admin_tree, list)
        admin_paths = {m.get("path") for m in admin_tree}
        assert "/system" in admin_paths

        demo_token = await _login(client, "demo", "Demo@123456")
        user_menus = await client.get(
            "/api/v1/menu/all",
            headers={"Authorization": f"Bearer {demo_token}"},
        )
        assert user_menus.status_code == 200
        user_tree = user_menus.json()["data"]
        user_paths = {m.get("path") for m in user_tree}
        assert "/system" not in user_paths
        assert "/chat" in user_paths or "/knowledge" in user_paths


@pytest.mark.asyncio
async def test_admin_roles_and_permissions() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client, "admin", "Admin@123456")
        headers = {"Authorization": f"Bearer {token}"}

        roles = await client.get("/api/v1/roles", headers=headers)
        assert roles.status_code == 200, roles.text
        assert any(r["code"] == "ADMIN" for r in roles.json()["data"]["items"])

        perms = await client.get(
            "/api/v1/permissions",
            headers=headers,
            params={"type": "MENU"},
        )
        assert perms.status_code == 200
        assert perms.json()["data"]["items"]

        code = f"menu:tmp_{uuid.uuid4().hex[:8]}"
        created = await client.post(
            "/api/v1/permissions",
            headers=headers,
            json={
                "code": code,
                "name": "Temp Menu",
                "type": "MENU",
                "path": f"/tmp/{uuid.uuid4().hex[:6]}",
                "visible": False,
            },
        )
        assert created.status_code == 200, created.text
        pid = created.json()["data"]["id"]
        deleted = await client.delete(f"/api/v1/permissions/{pid}", headers=headers)
        assert deleted.status_code == 200


@pytest.mark.asyncio
async def test_space_create_admin() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client, "admin", "Admin@123456")
        headers = {"Authorization": f"Bearer {token}"}
        name = f"Space-{uuid.uuid4().hex[:8]}"
        created = await client.post(
            "/api/v1/spaces",
            headers=headers,
            json={"name": name, "description": "m7"},
        )
        assert created.status_code == 200, created.text
        space_id = created.json()["data"]["id"]
        members = await client.get(
            f"/api/v1/spaces/{space_id}/members", headers=headers
        )
        assert members.status_code == 200
        assert members.json()["data"]["items"]
