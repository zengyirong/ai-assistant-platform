"""Org user routes (search / list / admin CRUD)."""

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
    email: str | None = Field(default=None, max_length=255)
    role_ids: list[str] | None = None


class UserUpdateRequest(BaseModel):
    nickname: str | None = Field(default=None, max_length=128)
    email: str | None = Field(default=None, max_length=255)
    status: str | None = None


class ResetPasswordRequest(BaseModel):
    password: str = Field(min_length=8, max_length=72)


class UserRolesRequest(BaseModel):
    role_ids: list[str] = Field(min_length=1)


@router.get("")
async def list_users(
    request: Request,
    q: str | None = Query(default=None, max_length=64),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_disabled: bool = Query(default=False),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await user_service.list_org_users(
        db,
        user,
        q=q,
        page=page,
        page_size=page_size,
        include_disabled=include_disabled,
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
            email=body.email,
            role_ids=body.role_ids,
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


@router.put("/{user_id}")
async def update_user(
    request: Request,
    user_id: str,
    body: UserUpdateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await user_service.update_org_user(
        db,
        user,
        user_id,
        nickname=body.nickname,
        email=body.email,
        status=body.status,
    )
    return ok(request, data)


@router.post("/{user_id}/reset-password")
async def reset_password(
    request: Request,
    user_id: str,
    body: ResetPasswordRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await user_service.reset_user_password(
        db, user, user_id, password=body.password
    )
    await audit_service.write_audit(
        action="user.reset_password",
        result="SUCCESS",
        org_id=user.org_id,
        user_id=user.id,
        resource_type="user",
        resource_id=user_id,
        request=request,
    )
    return ok(request, {})


@router.put("/{user_id}/roles")
async def set_user_roles(
    request: Request,
    user_id: str,
    body: UserRolesRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await user_service.set_user_roles(db, user, user_id, body.role_ids)
    await audit_service.write_audit(
        action="user.set_roles",
        result="SUCCESS",
        org_id=user.org_id,
        user_id=user.id,
        resource_type="user",
        resource_id=user_id,
        request=request,
        detail={"role_ids": body.role_ids},
    )
    return ok(request, data)
