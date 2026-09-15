"""Space list / admin CRUD (no nesting / dept)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.deps import CurrentUser
from app.core.errors import AppError
from app.core.rbac import is_admin
from app.models.base import new_id
from app.models.organization import Space, SpaceMember
from app.models.user import SysUser


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat(sep="T", timespec="milliseconds") if dt else None


def space_to_dict(space: Space) -> dict[str, Any]:
    return {
        "id": space.id,
        "org_id": space.org_id,
        "name": space.name,
        "description": space.description,
        "is_default": int(space.is_default or 0),
        "owner_id": space.owner_id,
        "created_at": _iso(space.created_at),
        "updated_at": _iso(space.updated_at),
    }


async def list_spaces(db: AsyncSession, user: CurrentUser) -> dict[str, Any]:
    result = await db.execute(
        select(Space)
        .where(Space.org_id == user.org_id)
        .order_by(Space.is_default.desc(), Space.created_at.asc())
    )
    items = [space_to_dict(s) for s in result.scalars().all()]
    return {"items": items}


async def create_space(
    db: AsyncSession,
    user: CurrentUser,
    *,
    name: str,
    description: str | None = None,
) -> dict[str, Any]:
    if not is_admin(user):
        raise AppError("PERMISSION_DENIED", "仅管理员可创建空间", http_status=403)
    name_norm = name.strip()
    if not name_norm:
        raise AppError("VALIDATION_ERROR", "空间名称不能为空", http_status=400)
    exists = await db.scalar(
        select(Space.id).where(Space.org_id == user.org_id, Space.name == name_norm)
    )
    if exists:
        raise AppError("SPACE_NAME_CONFLICT", "空间名称冲突", http_status=409)
    space = Space(
        id=new_id(),
        org_id=user.org_id,
        name=name_norm,
        description=(description or "").strip() or None,
        is_default=0,
        owner_id=user.id,
    )
    db.add(space)
    await db.flush()
    db.add(
        SpaceMember(
            id=new_id(),
            space_id=space.id,
            user_id=user.id,
            role="OWNER",
        )
    )
    await db.commit()
    await db.refresh(space)
    return space_to_dict(space)


async def update_space(
    db: AsyncSession,
    user: CurrentUser,
    space_id: str,
    *,
    name: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    if not is_admin(user):
        raise AppError("PERMISSION_DENIED", "仅管理员可修改空间", http_status=403)
    space = await db.scalar(
        select(Space).where(Space.id == space_id, Space.org_id == user.org_id)
    )
    if space is None:
        raise AppError("SPACE_NOT_FOUND", "空间不存在", http_status=404)
    if name is not None:
        name_norm = name.strip()
        if not name_norm:
            raise AppError("VALIDATION_ERROR", "空间名称不能为空", http_status=400)
        conflict = await db.scalar(
            select(Space.id).where(
                Space.org_id == user.org_id,
                Space.name == name_norm,
                Space.id != space_id,
            )
        )
        if conflict:
            raise AppError("SPACE_NAME_CONFLICT", "空间名称冲突", http_status=409)
        space.name = name_norm
    if description is not None:
        space.description = description.strip() or None
    await db.commit()
    await db.refresh(space)
    return space_to_dict(space)


async def list_space_members(
    db: AsyncSession,
    user: CurrentUser,
    space_id: str,
) -> dict[str, Any]:
    if not is_admin(user):
        raise AppError("PERMISSION_DENIED", "仅管理员可查看空间成员", http_status=403)
    space = await db.scalar(
        select(Space).where(Space.id == space_id, Space.org_id == user.org_id)
    )
    if space is None:
        raise AppError("SPACE_NOT_FOUND", "空间不存在", http_status=404)
    rows = (
        await db.execute(
            select(SpaceMember, SysUser)
            .join(SysUser, SysUser.id == SpaceMember.user_id)
            .where(SpaceMember.space_id == space_id)
            .order_by(SpaceMember.created_at.asc())
        )
    ).all()
    items = [
        {
            "id": member.id,
            "space_id": member.space_id,
            "user_id": member.user_id,
            "role": member.role,
            "username": u.username,
            "nickname": u.nickname,
        }
        for member, u in rows
    ]
    return {"items": items}


async def upsert_space_member(
    db: AsyncSession,
    user: CurrentUser,
    space_id: str,
    *,
    user_id: str,
    role: str = "MEMBER",
) -> dict[str, Any]:
    if not is_admin(user):
        raise AppError("PERMISSION_DENIED", "仅管理员可管理空间成员", http_status=403)
    if role not in {"OWNER", "MEMBER"}:
        raise AppError("VALIDATION_ERROR", "角色须为 OWNER 或 MEMBER", http_status=400)
    space = await db.scalar(
        select(Space).where(Space.id == space_id, Space.org_id == user.org_id)
    )
    if space is None:
        raise AppError("SPACE_NOT_FOUND", "空间不存在", http_status=404)
    target = await db.scalar(
        select(SysUser).where(SysUser.id == user_id, SysUser.org_id == user.org_id)
    )
    if target is None:
        raise AppError("USER_NOT_FOUND", "用户不存在", http_status=404)
    member = await db.scalar(
        select(SpaceMember).where(
            SpaceMember.space_id == space_id,
            SpaceMember.user_id == user_id,
        )
    )
    if member is None:
        member = SpaceMember(
            id=new_id(),
            space_id=space_id,
            user_id=user_id,
            role=role,
        )
        db.add(member)
    else:
        member.role = role
    await db.commit()
    return {
        "id": member.id,
        "space_id": space_id,
        "user_id": user_id,
        "role": role,
        "username": target.username,
        "nickname": target.nickname,
    }


async def remove_space_member(
    db: AsyncSession,
    user: CurrentUser,
    space_id: str,
    user_id: str,
) -> None:
    if not is_admin(user):
        raise AppError("PERMISSION_DENIED", "仅管理员可管理空间成员", http_status=403)
    space = await db.scalar(
        select(Space).where(Space.id == space_id, Space.org_id == user.org_id)
    )
    if space is None:
        raise AppError("SPACE_NOT_FOUND", "空间不存在", http_status=404)
    await db.execute(
        delete(SpaceMember).where(
            SpaceMember.space_id == space_id,
            SpaceMember.user_id == user_id,
        )
    )
    await db.commit()
