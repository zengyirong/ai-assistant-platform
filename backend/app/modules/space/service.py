"""Space list (Phase 1 slim)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.deps import CurrentUser
from app.models.organization import Space


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat(sep="T", timespec="milliseconds") if dt else None


def space_to_dict(space: Space) -> dict[str, Any]:
    return {
        "id": space.id,
        "org_id": space.org_id,
        "name": space.name,
        "description": space.description,
        "is_default": space.is_default,
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
