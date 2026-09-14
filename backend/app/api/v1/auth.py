"""Auth routes."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ok
from app.core.auth.deps import CurrentUser, get_current_user
from app.core.errors import AppError
from app.db.session import get_db
from app.modules.audit import service as audit_service
from app.modules.auth import service as auth_service

router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


@router.post("/login")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        data = await auth_service.login(
            db,
            username=body.username,
            password=body.password,
        )
    except AppError as exc:
        await audit_service.write_audit(
            action="auth.login",
            result="FAILED" if exc.code == "AUTH_UNAUTHORIZED" else "DENIED",
            detail={"username": body.username, "code": exc.code},
            request=request,
        )
        raise

    user = data["user"]
    await audit_service.write_audit(
        action="auth.login",
        result="SUCCESS",
        org_id=user.get("org_id"),
        user_id=user.get("id"),
        resource_type="user",
        resource_id=user.get("id"),
        detail={"username": user.get("username")},
        request=request,
    )
    return ok(request, data)


@router.post("/logout")
async def logout(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    await audit_service.write_audit(
        action="auth.logout",
        result="SUCCESS",
        org_id=user.org_id,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        request=request,
    )
    return ok(request, {})


@router.get("/me")
async def me(
    request: Request,
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    return ok(request, auth_service.me_payload(current))
