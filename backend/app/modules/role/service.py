"""Role admin services."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth.deps import CurrentUser
from app.core.errors import AppError
from app.core.rbac import is_admin
from app.models.base import new_id
from app.models.user import SysPermission, SysRole, SysRolePermission


def _require_admin(user: CurrentUser) -> None:
    if not is_admin(user):
        raise AppError(
            "PERMISSION_DENIED",
            "仅管理员可管理角色",
            http_status=403,
        )


def role_to_dict(role: SysRole, *, with_permissions: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": role.id,
        "org_id": role.org_id,
        "code": role.code,
        "name": role.name,
        "status": role.status,
        "created_at": (
            role.created_at.isoformat(sep="T", timespec="milliseconds")
            if role.created_at
            else None
        ),
        "updated_at": (
            role.updated_at.isoformat(sep="T", timespec="milliseconds")
            if role.updated_at
            else None
        ),
    }
    if with_permissions:
        data["permission_ids"] = [p.id for p in role.permissions]
        data["permission_codes"] = [p.code for p in role.permissions]
    return data


async def list_roles(
    db: AsyncSession,
    user: CurrentUser,
    *,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    _require_admin(user)
    base: Select[Any] = select(SysRole).where(SysRole.org_id == user.org_id)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    result = await db.execute(
        base.options(selectinload(SysRole.permissions))
        .order_by(SysRole.code.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [
        role_to_dict(r, with_permissions=True) for r in result.scalars().all()
    ]
    return {
        "items": items,
        "total": int(total or 0),
        "page": page,
        "page_size": page_size,
    }


async def create_role(
    db: AsyncSession,
    user: CurrentUser,
    *,
    code: str,
    name: str,
    status: str = "ACTIVE",
) -> dict[str, Any]:
    _require_admin(user)
    code_norm = code.strip().upper()
    if not code_norm:
        raise AppError("VALIDATION_ERROR", "角色编码不能为空", http_status=400)
    exists = await db.scalar(
        select(SysRole.id).where(
            SysRole.org_id == user.org_id,
            SysRole.code == code_norm,
        )
    )
    if exists:
        raise AppError("ROLE_CODE_CONFLICT", "角色编码已存在", http_status=409)
    role = SysRole(
        id=new_id(),
        org_id=user.org_id,
        code=code_norm,
        name=name.strip() or code_norm,
        status=status if status in {"ACTIVE", "DISABLED"} else "ACTIVE",
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role_to_dict(role, with_permissions=True)


async def update_role(
    db: AsyncSession,
    user: CurrentUser,
    role_id: str,
    *,
    name: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    _require_admin(user)
    role = await db.scalar(
        select(SysRole)
        .where(SysRole.id == role_id, SysRole.org_id == user.org_id)
        .options(selectinload(SysRole.permissions))
    )
    if role is None:
        raise AppError("ROLE_NOT_FOUND", "角色不存在", http_status=404)
    if role.code in {"ADMIN", "USER"} and status == "DISABLED":
        raise AppError(
            "VALIDATION_ERROR",
            "系统内置角色不可停用",
            http_status=400,
        )
    if name is not None:
        role.name = name.strip() or role.name
    if status is not None and status in {"ACTIVE", "DISABLED"}:
        role.status = status
    await db.commit()
    await db.refresh(role)
    return role_to_dict(role, with_permissions=True)


async def set_role_permissions(
    db: AsyncSession,
    user: CurrentUser,
    role_id: str,
    permission_ids: list[str],
) -> dict[str, Any]:
    _require_admin(user)
    role = await db.scalar(
        select(SysRole).where(SysRole.id == role_id, SysRole.org_id == user.org_id)
    )
    if role is None:
        raise AppError("ROLE_NOT_FOUND", "角色不存在", http_status=404)

    ids = list({pid for pid in permission_ids if pid})
    if ids:
        found = (
            await db.execute(select(SysPermission.id).where(SysPermission.id.in_(ids)))
        ).scalars().all()
        if len(found) != len(ids):
            raise AppError("VALIDATION_ERROR", "存在无效权限 ID", http_status=400)

    await db.execute(
        delete(SysRolePermission).where(SysRolePermission.role_id == role_id)
    )
    for pid in ids:
        db.add(SysRolePermission(id=new_id(), role_id=role_id, permission_id=pid))
    await db.commit()

    role = await db.scalar(
        select(SysRole)
        .where(SysRole.id == role_id)
        .options(selectinload(SysRole.permissions))
    )
    assert role is not None
    return role_to_dict(role, with_permissions=True)
