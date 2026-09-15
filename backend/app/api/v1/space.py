"""Space routes."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ok
from app.core.auth.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.modules.space import service as space_service

router = APIRouter()

MemberRole = Literal["OWNER", "MEMBER"]


class SpaceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=512)


class SpaceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=512)


class SpaceMemberRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=36)
    role: MemberRole = "MEMBER"


@router.get("")
async def list_spaces(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await space_service.list_spaces(db, user)
    return ok(request, data)


@router.post("")
async def create_space(
    request: Request,
    body: SpaceCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await space_service.create_space(
        db, user, name=body.name, description=body.description
    )
    return ok(request, data)


@router.put("/{space_id}")
async def update_space(
    request: Request,
    space_id: str,
    body: SpaceUpdateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await space_service.update_space(
        db, user, space_id, name=body.name, description=body.description
    )
    return ok(request, data)


@router.get("/{space_id}/members")
async def list_members(
    request: Request,
    space_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await space_service.list_space_members(db, user, space_id)
    return ok(request, data)


@router.post("/{space_id}/members")
async def upsert_member(
    request: Request,
    space_id: str,
    body: SpaceMemberRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await space_service.upsert_space_member(
        db, user, space_id, user_id=body.user_id, role=body.role
    )
    return ok(request, data)


@router.delete("/{space_id}/members/{member_user_id}")
async def remove_member(
    request: Request,
    space_id: str,
    member_user_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await space_service.remove_space_member(db, user, space_id, member_user_id)
    return ok(request, {})
