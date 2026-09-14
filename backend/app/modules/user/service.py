"""Org user list / search for collaboration UX."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.deps import CurrentUser
from app.models.user import SysUser


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
