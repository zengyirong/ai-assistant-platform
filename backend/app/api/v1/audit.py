"""Audit log routes (ADMIN read)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ok
from app.core.auth.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.modules.audit import service as audit_service

router = APIRouter()


@router.get("")
async def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str | None = Query(default=None, max_length=64),
    user_id: str | None = Query(default=None, max_length=36),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await audit_service.list_audit_logs(
        db,
        user,
        page=page,
        page_size=page_size,
        action=action,
        user_id=user_id,
    )
    return ok(request, data)
