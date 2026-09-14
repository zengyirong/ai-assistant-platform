"""Org user routes (search / list / thin create for member pickers)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ok
from app.core.auth.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.modules.audit import service as audit_service
from app.modules.user import service as user_service

router = APIRouter()


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=72)
    nickname: str | None = Field(default=None, max_length=128)


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


@router.post("")
async def create_user(
    request: Request,
    body: UserCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        data = await user_service.create_org_user(
            db,
            user,
            username=body.username,
            password=body.password,
            nickname=body.nickname,
        )
    except Exception:
        await audit_service.write_audit(
            action="user.create",
            result="FAILED",
            org_id=user.org_id,
            user_id=user.id,
            resource_type="user",
            request=request,
            detail={"username": body.username},
        )
        raise

    await audit_service.write_audit(
        action="user.create",
        result="SUCCESS",
        org_id=user.org_id,
        user_id=user.id,
        resource_type="user",
        resource_id=data["id"],
        request=request,
        detail={"username": data["username"]},
    )
    return ok(request, data)
