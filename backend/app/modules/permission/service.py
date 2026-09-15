"""Permission / menu tree services (sys_permission as single source)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth.deps import CurrentUser
from app.core.errors import AppError
from app.core.rbac import is_admin
from app.models.base import new_id
from app.models.user import SysPermission, SysRole, SysUser

MENU_TYPES = {"MENU", "BUTTON", "API"}


def permission_to_dict(row: SysPermission) -> dict[str, Any]:
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "type": row.type,
        "parent_id": row.parent_id,
        "path": row.path,
        "component": row.component,
        "icon": row.icon,
        "sort_order": row.sort_order,
        "visible": bool(row.visible),
        "status": row.status,
        "redirect": row.redirect,
    }


def _require_admin(user: CurrentUser) -> None:
    if not is_admin(user):
        raise AppError(
            "PERMISSION_DENIED",
            "仅管理员可管理权限/菜单",
            http_status=403,
        )


async def list_permissions(
    db: AsyncSession,
    user: CurrentUser,
    *,
    type_filter: str | None = None,
) -> dict[str, Any]:
    _require_admin(user)
    stmt = select(SysPermission).order_by(
        SysPermission.sort_order.asc(), SysPermission.code.asc()
    )
    if type_filter:
        stmt = stmt.where(SysPermission.type == type_filter.strip().upper())
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": [permission_to_dict(r) for r in rows]}


def build_tree(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {i["id"]: {**i, "children": []} for i in items}
    roots: list[dict[str, Any]] = []
    for node in by_id.values():
        parent_id = node.get("parent_id")
        if parent_id and parent_id in by_id:
            by_id[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


async def list_permission_tree(
    db: AsyncSession,
    user: CurrentUser,
    *,
    type_filter: str | None = None,
) -> dict[str, Any]:
    data = await list_permissions(db, user, type_filter=type_filter)
    return {"items": build_tree(data["items"])}


async def create_permission(
    db: AsyncSession,
    user: CurrentUser,
    *,
    code: str,
    name: str,
    type: str,
    parent_id: str | None = None,
    path: str | None = None,
    component: str | None = None,
    icon: str | None = None,
    sort_order: int = 0,
    visible: bool = True,
    status: str = "ACTIVE",
    redirect: str | None = None,
) -> dict[str, Any]:
    _require_admin(user)
    perm_type = type.strip().upper()
    if perm_type not in MENU_TYPES:
        raise AppError("VALIDATION_ERROR", "type 须为 MENU/BUTTON/API", http_status=400)
    code_norm = code.strip()
    if not code_norm:
        raise AppError("VALIDATION_ERROR", "code 不能为空", http_status=400)
    exists = await db.scalar(
        select(SysPermission.id).where(SysPermission.code == code_norm)
    )
    if exists:
        raise AppError(
            "PERMISSION_CODE_CONFLICT",
            "权限码已存在",
            http_status=409,
        )
    if parent_id:
        parent = await db.get(SysPermission, parent_id)
        if parent is None:
            raise AppError("VALIDATION_ERROR", "父节点不存在", http_status=400)

    row = SysPermission(
        id=new_id(),
        code=code_norm,
        name=name.strip(),
        type=perm_type,
        parent_id=parent_id,
        path=(path or "").strip() or None,
        component=(component or "").strip() or None,
        icon=(icon or "").strip() or None,
        sort_order=sort_order,
        visible=1 if visible else 0,
        status=status if status in {"ACTIVE", "DISABLED"} else "ACTIVE",
        redirect=(redirect or "").strip() or None,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return permission_to_dict(row)


async def update_permission(
    db: AsyncSession,
    user: CurrentUser,
    permission_id: str,
    *,
    name: str | None = None,
    parent_id: str | None = None,
    path: str | None = None,
    component: str | None = None,
    icon: str | None = None,
    sort_order: int | None = None,
    visible: bool | None = None,
    status: str | None = None,
    redirect: str | None = None,
    clear_parent: bool = False,
) -> dict[str, Any]:
    _require_admin(user)
    row = await db.get(SysPermission, permission_id)
    if row is None:
        raise AppError("PERMISSION_NOT_FOUND", "权限/菜单不存在", http_status=404)
    if name is not None:
        row.name = name.strip()
    if clear_parent:
        row.parent_id = None
    elif parent_id is not None:
        if parent_id == row.id:
            raise AppError("VALIDATION_ERROR", "不能将自身设为父节点", http_status=400)
        row.parent_id = parent_id
    if path is not None:
        row.path = path.strip() or None
    if component is not None:
        row.component = component.strip() or None
    if icon is not None:
        row.icon = icon.strip() or None
    if sort_order is not None:
        row.sort_order = sort_order
    if visible is not None:
        row.visible = 1 if visible else 0
    if status is not None:
        row.status = status if status in {"ACTIVE", "DISABLED"} else row.status
    if redirect is not None:
        row.redirect = redirect.strip() or None
    await db.commit()
    await db.refresh(row)
    return permission_to_dict(row)


async def delete_permission(
    db: AsyncSession,
    user: CurrentUser,
    permission_id: str,
) -> None:
    _require_admin(user)
    row = await db.get(SysPermission, permission_id)
    if row is None:
        raise AppError("PERMISSION_NOT_FOUND", "权限/菜单不存在", http_status=404)
    child = await db.scalar(
        select(SysPermission.id).where(SysPermission.parent_id == permission_id).limit(1)
    )
    if child:
        raise AppError(
            "VALIDATION_ERROR",
            "请先删除子节点",
            http_status=400,
        )
    await db.delete(row)
    await db.commit()


async def menus_for_user(
    db: AsyncSession,
    user: CurrentUser,
) -> list[dict[str, Any]]:
    """Build Vben route tree from MENU permissions granted to the user."""
    stmt = (
        select(SysUser)
        .where(SysUser.id == user.id)
        .options(
            selectinload(SysUser.roles).selectinload(SysRole.permissions),
        )
    )
    db_user = (await db.execute(stmt)).scalar_one_or_none()
    if db_user is None:
        return []

    granted: dict[str, SysPermission] = {}
    for role in db_user.roles:
        if role.status != "ACTIVE":
            continue
        for perm in role.permissions:
            if (
                perm.type == "MENU"
                and perm.status == "ACTIVE"
                and perm.id not in granted
            ):
                granted[perm.id] = perm

    if not granted:
        return []

    # Include ancestors so catalogs appear when any leaf is granted
    all_rows = (await db.execute(select(SysPermission))).scalars().all()
    by_id = {r.id: r for r in all_rows}
    needed = dict(granted)
    for node in list(granted.values()):
        pid = node.parent_id
        while pid and pid not in needed and pid in by_id:
            parent = by_id[pid]
            if parent.type == "MENU" and parent.status == "ACTIVE":
                needed[pid] = parent
            pid = parent.parent_id

    nodes = [
        permission_to_dict(r)
        for r in needed.values()
        if r.type == "MENU" and r.status == "ACTIVE"
    ]
    nodes.sort(key=lambda n: (n["sort_order"], n["code"]))
    tree = build_tree(nodes)
    return [_to_vben_route(n) for n in tree]


def _to_vben_route(node: dict[str, Any]) -> dict[str, Any]:
    children_raw = node.get("children") or []
    children = [_to_vben_route(c) for c in children_raw]
    meta: dict[str, Any] = {
        "title": node["name"],
        "icon": node.get("icon") or None,
        "order": node.get("sort_order") or 0,
        "hideInMenu": not node.get("visible", True),
    }
    route: dict[str, Any] = {
        "name": node["code"].replace(":", "_").replace("-", "_"),
        "path": node.get("path") or f"/{node['code']}",
        "meta": meta,
    }
    if node.get("redirect"):
        route["redirect"] = node["redirect"]
    if children:
        route["children"] = children
    elif node.get("component"):
        route["component"] = node["component"]
    return route
