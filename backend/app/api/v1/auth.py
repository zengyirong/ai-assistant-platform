"""Auth routes — scaffold stubs for Phase 1."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.errors import AppError

router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


@router.post("/login")
async def login(body: LoginRequest) -> dict:
    # Phase 1: verify against sys_user + issue JWT
    raise AppError(
        "AUTH_UNAUTHORIZED",
        "认证尚未实现，请等待 Phase 1 Auth 模块",
        http_status=401,
    )


@router.post("/logout")
async def logout() -> dict:
    return {
        "code": "OK",
        "message": "success",
        "data": {},
        "request_id": "pending",
    }


@router.get("/me")
async def me() -> dict:
    raise AppError(
        "AUTH_UNAUTHORIZED",
        "认证尚未实现，请等待 Phase 1 Auth 模块",
        http_status=401,
    )
