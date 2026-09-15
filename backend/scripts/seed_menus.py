"""Idempotent seed of MENU permissions + role bindings (M7)."""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.base import new_id
from app.models.user import SysPermission, SysRolePermission

ADMIN_ROLE = "33333333-3333-3333-3333-333333333333"
USER_ROLE = "44444444-4444-4444-4444-444444444444"

MENUS: list[dict] = [
    {
        "id": "m0000000-0000-0000-0000-000000000001",
        "code": "menu:dashboard",
        "name": "工作台",
        "type": "MENU",
        "parent_id": None,
        "path": "/dashboard",
        "component": None,
        "icon": "lucide:layout-dashboard",
        "sort_order": -1,
        "visible": 1,
        "status": "ACTIVE",
        "redirect": "/dashboard/home",
    },
    {
        "id": "m0000000-0000-0000-0000-000000000002",
        "code": "menu:dashboard:home",
        "name": "首页",
        "type": "MENU",
        "parent_id": "m0000000-0000-0000-0000-000000000001",
        "path": "/dashboard/home",
        "component": "/dashboard/index",
        "icon": "lucide:home",
        "sort_order": 0,
        "visible": 1,
        "status": "ACTIVE",
        "redirect": None,
    },
    {
        "id": "m0000000-0000-0000-0000-000000000010",
        "code": "menu:chat",
        "name": "智能问答",
        "type": "MENU",
        "parent_id": None,
        "path": "/chat",
        "component": None,
        "icon": "lucide:message-square-text",
        "sort_order": 5,
        "visible": 1,
        "status": "ACTIVE",
        "redirect": "/chat/workspace",
    },
    {
        "id": "m0000000-0000-0000-0000-000000000011",
        "code": "menu:chat:workspace",
        "name": "问答工作台",
        "type": "MENU",
        "parent_id": "m0000000-0000-0000-0000-000000000010",
        "path": "/chat/workspace",
        "component": "/ai-chat/index",
        "icon": "lucide:bot",
        "sort_order": 0,
        "visible": 1,
        "status": "ACTIVE",
        "redirect": None,
    },
    {
        "id": "m0000000-0000-0000-0000-000000000020",
        "code": "menu:knowledge",
        "name": "知识库",
        "type": "MENU",
        "parent_id": None,
        "path": "/knowledge",
        "component": None,
        "icon": "lucide:library",
        "sort_order": 10,
        "visible": 1,
        "status": "ACTIVE",
        "redirect": "/knowledge/list",
    },
    {
        "id": "m0000000-0000-0000-0000-000000000021",
        "code": "menu:knowledge:list",
        "name": "知识库管理",
        "type": "MENU",
        "parent_id": "m0000000-0000-0000-0000-000000000020",
        "path": "/knowledge/list",
        "component": "/knowledge/list",
        "icon": "lucide:folder-kanban",
        "sort_order": 0,
        "visible": 1,
        "status": "ACTIVE",
        "redirect": None,
    },
    {
        "id": "m0000000-0000-0000-0000-000000000022",
        "code": "menu:knowledge:detail",
        "name": "知识库详情",
        "type": "MENU",
        "parent_id": "m0000000-0000-0000-0000-000000000020",
        "path": "/knowledge/detail/:kbId",
        "component": "/knowledge/detail",
        "icon": "lucide:file-text",
        "sort_order": 1,
        "visible": 0,
        "status": "ACTIVE",
        "redirect": None,
    },
    {
        "id": "m0000000-0000-0000-0000-000000000030",
        "code": "menu:system",
        "name": "系统管理",
        "type": "MENU",
        "parent_id": None,
        "path": "/system",
        "component": None,
        "icon": "lucide:settings",
        "sort_order": 30,
        "visible": 1,
        "status": "ACTIVE",
        "redirect": "/system/user",
    },
    {
        "id": "m0000000-0000-0000-0000-000000000031",
        "code": "menu:system:user",
        "name": "用户管理",
        "type": "MENU",
        "parent_id": "m0000000-0000-0000-0000-000000000030",
        "path": "/system/user",
        "component": "/system/user/index",
        "icon": "lucide:users",
        "sort_order": 0,
        "visible": 1,
        "status": "ACTIVE",
        "redirect": None,
    },
    {
        "id": "m0000000-0000-0000-0000-000000000032",
        "code": "menu:system:role",
        "name": "角色管理",
        "type": "MENU",
        "parent_id": "m0000000-0000-0000-0000-000000000030",
        "path": "/system/role",
        "component": "/system/role/index",
        "icon": "lucide:shield",
        "sort_order": 1,
        "visible": 1,
        "status": "ACTIVE",
        "redirect": None,
    },
    {
        "id": "m0000000-0000-0000-0000-000000000033",
        "code": "menu:system:menu",
        "name": "菜单管理",
        "type": "MENU",
        "parent_id": "m0000000-0000-0000-0000-000000000030",
        "path": "/system/menu",
        "component": "/system/menu/index",
        "icon": "lucide:menu",
        "sort_order": 2,
        "visible": 1,
        "status": "ACTIVE",
        "redirect": None,
    },
    {
        "id": "m0000000-0000-0000-0000-000000000034",
        "code": "menu:system:space",
        "name": "空间管理",
        "type": "MENU",
        "parent_id": "m0000000-0000-0000-0000-000000000030",
        "path": "/system/space",
        "component": "/system/space/index",
        "icon": "lucide:boxes",
        "sort_order": 3,
        "visible": 1,
        "status": "ACTIVE",
        "redirect": None,
    },
    {
        "id": "m0000000-0000-0000-0000-000000000035",
        "code": "menu:system:audit",
        "name": "审计日志",
        "type": "MENU",
        "parent_id": "m0000000-0000-0000-0000-000000000030",
        "path": "/system/audit",
        "component": "/system/audit/index",
        "icon": "lucide:scroll-text",
        "sort_order": 4,
        "visible": 1,
        "status": "ACTIVE",
        "redirect": None,
    },
]

USER_MENU_IDS = {
    "m0000000-0000-0000-0000-000000000001",
    "m0000000-0000-0000-0000-000000000002",
    "m0000000-0000-0000-0000-000000000010",
    "m0000000-0000-0000-0000-000000000011",
    "m0000000-0000-0000-0000-000000000020",
    "m0000000-0000-0000-0000-000000000021",
    "m0000000-0000-0000-0000-000000000022",
}


async def seed_menus() -> int:
    async with AsyncSessionLocal() as db:
        for item in MENUS:
            row = await db.get(SysPermission, item["id"])
            if row is None:
                db.add(SysPermission(**item))
            else:
                for key, value in item.items():
                    if key != "id":
                        setattr(row, key, value)
        await db.flush()
        menus = (
            await db.execute(select(SysPermission).where(SysPermission.type == "MENU"))
        ).scalars().all()
        for role_id, allow in ((ADMIN_ROLE, None), (USER_ROLE, USER_MENU_IDS)):
            for perm in menus:
                if allow is not None and perm.id not in allow:
                    continue
                exists = await db.scalar(
                    select(SysRolePermission.id).where(
                        SysRolePermission.role_id == role_id,
                        SysRolePermission.permission_id == perm.id,
                    )
                )
                if not exists:
                    db.add(
                        SysRolePermission(
                            id=new_id(),
                            role_id=role_id,
                            permission_id=perm.id,
                        )
                    )
        await db.commit()
        return len(menus)


def main() -> None:
    count = asyncio.run(seed_menus())
    print(f"seeded {count} MENU permissions")


if __name__ == "__main__":
    main()
