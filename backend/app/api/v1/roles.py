"""Role admin routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ok
from app.core.auth.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.modules.role import service as role_service

router = APIRouter()


class RoleCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    status: str = "ACTIVE"


class RoleUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    status: str | None = None


class RolePermissionsRequest(BaseModel):
    permission_ids: list[str] = Field(default_factory=list)


@router.get("")
async def list_roles(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await role_service.list_roles(db, user, page=page, page_size=page_size)
    return ok(request, data)


@router.post("")
async def create_role(
    request: Request,
    body: RoleCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await role_service.create_role(
        db, user, code=body.code, name=body.name, status=body.status
    )
    return ok(request, data)


@router.put("/{role_id}")
async def update_role(
    request: Request,
    role_id: str,
    body: RoleUpdateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await role_service.update_role(
        db, user, role_id, name=body.name, status=body.status
    )
    return ok(request, data)


@router.put("/{role_id}/permissions")
async def set_role_permissions(
    request: Request,
    role_id: str,
    body: RolePermissionsRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await role_service.set_role_permissions(
        db, user, role_id, body.permission_ids
    )
    return ok(request, data)
