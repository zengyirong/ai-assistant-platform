"""Permission / menu admin routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ok
from app.core.auth.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.modules.permission import service as permission_service

router = APIRouter()
menu_router = APIRouter()


class PermissionCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    type: str = Field(min_length=1, max_length=32)
    parent_id: str | None = None
    path: str | None = Field(default=None, max_length=255)
    component: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=128)
    sort_order: int = 0
    visible: bool = True
    status: str = "ACTIVE"
    redirect: str | None = Field(default=None, max_length=255)


class PermissionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    parent_id: str | None = None
    clear_parent: bool = False
    path: str | None = Field(default=None, max_length=255)
    component: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=128)
    sort_order: int | None = None
    visible: bool | None = None
    status: str | None = None
    redirect: str | None = Field(default=None, max_length=255)


@router.get("")
async def list_permissions(
    request: Request,
    type: str | None = Query(default=None, max_length=32),
    tree: bool = Query(default=False),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if tree:
        data = await permission_service.list_permission_tree(
            db, user, type_filter=type
        )
    else:
        data = await permission_service.list_permissions(db, user, type_filter=type)
    return ok(request, data)


@router.post("")
async def create_permission(
    request: Request,
    body: PermissionCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await permission_service.create_permission(
        db,
        user,
        code=body.code,
        name=body.name,
        type=body.type,
        parent_id=body.parent_id,
        path=body.path,
        component=body.component,
        icon=body.icon,
        sort_order=body.sort_order,
        visible=body.visible,
        status=body.status,
        redirect=body.redirect,
    )
    return ok(request, data)


@router.put("/{permission_id}")
async def update_permission(
    request: Request,
    permission_id: str,
    body: PermissionUpdateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await permission_service.update_permission(
        db,
        user,
        permission_id,
        name=body.name,
        parent_id=body.parent_id,
        clear_parent=body.clear_parent,
        path=body.path,
        component=body.component,
        icon=body.icon,
        sort_order=body.sort_order,
        visible=body.visible,
        status=body.status,
        redirect=body.redirect,
    )
    return ok(request, data)


@router.delete("/{permission_id}")
async def delete_permission(
    request: Request,
    permission_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await permission_service.delete_permission(db, user, permission_id)
    return ok(request, {})


@menu_router.get("/all")
async def menu_all(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await permission_service.menus_for_user(db, user)
    return ok(request, data)
