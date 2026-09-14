"""Org user routes (search / list for member pickers)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ok
from app.core.auth.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.modules.user import service as user_service

router = APIRouter()


@router.get("")
async def list_users(
    request: Request,
    q: str | None = Query(default=None, max_length=64),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await user_service.list_org_users(
        db, user, q=q, page=page, page_size=page_size
    )
    return ok(request, data)
