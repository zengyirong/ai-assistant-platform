"""Auth routes."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ok
from app.core.auth.deps import CurrentUser, get_current_user
from app.db.session import get_db
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
    data = await auth_service.login(
        db,
        username=body.username,
        password=body.password,
    )
    return ok(request, data)


@router.post("/logout")
async def logout(
    request: Request,
    _user: CurrentUser = Depends(get_current_user),
) -> dict:
    # JWT is stateless in Phase 1; client discards token. Audit later.
    return ok(request, {})


@router.get("/me")
async def me(
    request: Request,
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    return ok(request, auth_service.me_payload(current))
