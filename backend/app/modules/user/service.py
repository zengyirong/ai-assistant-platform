"""Org user list / search / thin create for collaboration UX."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.deps import CurrentUser
from app.core.errors import AppError
from app.core.rbac import is_admin
from app.core.security import hash_password
from app.models.base import new_id
from app.models.user import SysRole, SysUser, SysUserRole

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


def user_brief_dict(user: SysUser) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "status": user.status,
    }


async def list_org_users(
    db: AsyncSession,
    current: CurrentUser,
    *,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """List ACTIVE users in the current org (optional username/nickname search)."""
    filters = [
        SysUser.org_id == current.org_id,
        SysUser.status == "ACTIVE",
    ]
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
        base.order_by(SysUser.username.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [user_brief_dict(u) for u in result.scalars().all()]
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
) -> dict[str, Any]:
    """ADMIN-only: create ACTIVE USER in the same org (no full admin UI)."""
    if not is_admin(current):
        raise AppError(
            "PERMISSION_DENIED",
            "仅管理员可创建用户",
            http_status=403,
        )

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

    # Login looks up username globally — keep unique across orgs for Phase 1.
    existing = await db.scalar(select(SysUser.id).where(SysUser.username == name))
    if existing is not None:
        raise AppError(
            "USER_NAME_CONFLICT",
            "用户名已存在",
            http_status=409,
        )

    role = await db.scalar(
        select(SysRole).where(
            SysRole.org_id == current.org_id,
            SysRole.code == "USER",
            SysRole.status == "ACTIVE",
        )
    )
    if role is None:
        raise AppError(
            "INTERNAL_ERROR",
            "组织缺少 USER 角色，请检查种子数据",
            http_status=500,
        )

    user = SysUser(
        id=new_id(),
        org_id=current.org_id,
        username=name,
        password_hash=hash_password(password),
        nickname=(nickname or "").strip() or name,
        status="ACTIVE",
    )
    db.add(user)
    await db.flush()
    db.add(SysUserRole(id=new_id(), user_id=user.id, role_id=role.id))
    await db.commit()
    await db.refresh(user)
    return user_brief_dict(user)
