"""Org user list / search / admin CRUD for system management."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth.deps import CurrentUser
from app.core.errors import AppError
from app.core.rbac import is_admin
from app.core.security import hash_password
from app.models.base import new_id
from app.models.user import SysRole, SysUser, SysUserRole

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


def _require_admin(user: CurrentUser) -> None:
    if not is_admin(user):
        raise AppError(
            "PERMISSION_DENIED",
            "仅管理员可管理用户",
            http_status=403,
        )


def user_brief_dict(user: SysUser, *, with_roles: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "status": user.status,
        "org_id": user.org_id,
        "created_at": (
            user.created_at.isoformat(sep="T", timespec="milliseconds")
            if user.created_at
            else None
        ),
    }
    if with_roles:
        data["roles"] = [r.code for r in user.roles if r.status == "ACTIVE"]
        data["role_ids"] = [r.id for r in user.roles]
    return data


async def list_org_users(
    db: AsyncSession,
    current: CurrentUser,
    *,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
    include_disabled: bool = False,
) -> dict[str, Any]:
    """List users in the current org (member picker defaults to ACTIVE only)."""
    filters = [SysUser.org_id == current.org_id]
    if not include_disabled or not is_admin(current):
        filters.append(SysUser.status == "ACTIVE")
    keyword = (q or "").strip()
    if keyword:
        like = f"%{keyword}%"
        filters.append(
            or_(
                SysUser.username.like(like),
                SysUser.nickname.like(like),
            )
        )

    base: Select[Any] = select(SysUser).where(*filters)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    result = await db.execute(
        base.options(selectinload(SysUser.roles))
        .order_by(SysUser.username.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    with_roles = is_admin(current) and include_disabled
    items = [
        user_brief_dict(u, with_roles=with_roles or is_admin(current))
        for u in result.scalars().all()
    ]
    return {
        "items": items,
        "total": int(total or 0),
        "page": page,
        "page_size": page_size,
    }


async def create_org_user(
    db: AsyncSession,
    current: CurrentUser,
    *,
    username: str,
    password: str,
    nickname: str | None = None,
    email: str | None = None,
    role_ids: list[str] | None = None,
) -> dict[str, Any]:
    """ADMIN-only: create user in the same org."""
    _require_admin(current)

    name = username.strip()
    if not _USERNAME_RE.match(name):
        raise AppError(
            "VALIDATION_ERROR",
            "用户名须为 3–32 位字母、数字或下划线",
            http_status=400,
        )
    if len(password.encode("utf-8")) < 8:
        raise AppError(
            "VALIDATION_ERROR",
            "密码至少 8 个字符",
            http_status=400,
        )

    existing = await db.scalar(select(SysUser.id).where(SysUser.username == name))
    if existing is not None:
        raise AppError(
            "USER_NAME_CONFLICT",
            "用户名已存在",
            http_status=409,
        )

    user = SysUser(
        id=new_id(),
        org_id=current.org_id,
        username=name,
        password_hash=hash_password(password),
        nickname=(nickname or "").strip() or name,
        email=(email or "").strip() or None,
        status="ACTIVE",
    )
    db.add(user)
    await db.flush()

    target_role_ids = role_ids
    if not target_role_ids:
        default_role = await db.scalar(
            select(SysRole).where(
                SysRole.org_id == current.org_id,
                SysRole.code == "USER",
                SysRole.status == "ACTIVE",
            )
        )
        if default_role is None:
            raise AppError(
                "INTERNAL_ERROR",
                "组织缺少 USER 角色，请检查种子数据",
                http_status=500,
            )
        target_role_ids = [default_role.id]
    else:
        roles = (
            await db.execute(
                select(SysRole).where(
                    SysRole.org_id == current.org_id,
                    SysRole.id.in_(target_role_ids),
                )
            )
        ).scalars().all()
        if len(roles) != len(set(target_role_ids)):
            raise AppError("VALIDATION_ERROR", "存在无效角色", http_status=400)

    for rid in set(target_role_ids):
        db.add(SysUserRole(id=new_id(), user_id=user.id, role_id=rid))

    await db.commit()
    user = await db.scalar(
        select(SysUser)
        .where(SysUser.id == user.id)
        .options(selectinload(SysUser.roles))
    )
    assert user is not None
    return user_brief_dict(user, with_roles=True)


async def update_org_user(
    db: AsyncSession,
    current: CurrentUser,
    user_id: str,
    *,
    nickname: str | None = None,
    email: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    _require_admin(current)
    user = await db.scalar(
        select(SysUser)
        .where(SysUser.id == user_id, SysUser.org_id == current.org_id)
        .options(selectinload(SysUser.roles))
    )
    if user is None:
        raise AppError("USER_NOT_FOUND", "用户不存在", http_status=404)
    if user.id == current.id and status == "DISABLED":
        raise AppError("VALIDATION_ERROR", "不能停用当前登录账号", http_status=400)
    if nickname is not None:
        user.nickname = nickname.strip() or user.nickname
    if email is not None:
        user.email = email.strip() or None
    if status is not None and status in {"ACTIVE", "DISABLED"}:
        user.status = status
    await db.commit()
    await db.refresh(user)
    return user_brief_dict(user, with_roles=True)


async def reset_user_password(
    db: AsyncSession,
    current: CurrentUser,
    user_id: str,
    *,
    password: str,
) -> None:
    _require_admin(current)
    if len(password.encode("utf-8")) < 8:
        raise AppError("VALIDATION_ERROR", "密码至少 8 个字符", http_status=400)
    user = await db.scalar(
        select(SysUser).where(SysUser.id == user_id, SysUser.org_id == current.org_id)
    )
    if user is None:
        raise AppError("USER_NOT_FOUND", "用户不存在", http_status=404)
    user.password_hash = hash_password(password)
    await db.commit()


async def set_user_roles(
    db: AsyncSession,
    current: CurrentUser,
    user_id: str,
    role_ids: list[str],
) -> dict[str, Any]:
    _require_admin(current)
    user = await db.scalar(
        select(SysUser).where(SysUser.id == user_id, SysUser.org_id == current.org_id)
    )
    if user is None:
        raise AppError("USER_NOT_FOUND", "用户不存在", http_status=404)
    ids = list({rid for rid in role_ids if rid})
    if not ids:
        raise AppError("VALIDATION_ERROR", "至少保留一个角色", http_status=400)
    roles = (
        await db.execute(
            select(SysRole).where(SysRole.org_id == current.org_id, SysRole.id.in_(ids))
        )
    ).scalars().all()
    if len(roles) != len(ids):
        raise AppError("VALIDATION_ERROR", "存在无效角色", http_status=400)

    await db.execute(delete(SysUserRole).where(SysUserRole.user_id == user_id))
    for rid in ids:
        db.add(SysUserRole(id=new_id(), user_id=user_id, role_id=rid))
    await db.commit()

    user = await db.scalar(
        select(SysUser)
        .where(SysUser.id == user_id)
        .options(selectinload(SysUser.roles))
    )
    assert user is not None
    return user_brief_dict(user, with_roles=True)
