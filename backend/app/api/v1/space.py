"""Space routes (Phase 1 slim: list only)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ok
from app.core.auth.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.modules.space import service as space_service

router = APIRouter()


@router.get("")
async def list_spaces(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await space_service.list_spaces(db, user)
    return ok(request, data)
