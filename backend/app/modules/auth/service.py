"""Auth application service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth.deps import CurrentUser
from app.core.errors import AppError
from app.core.security import create_access_token, verify_password
from app.models.user import SysRole, SysUser


async def authenticate_user(
    db: AsyncSession,
    *,
    username: str,
    password: str,
) -> SysUser:
    stmt = (
        select(SysUser)
        .where(SysUser.username == username)
        .options(selectinload(SysUser.roles).selectinload(SysRole.permissions))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None or user.status != "ACTIVE":
        raise AppError("AUTH_UNAUTHORIZED", "用户名或密码错误", http_status=401)
    if not verify_password(password, user.password_hash):
        raise AppError("AUTH_UNAUTHORIZED", "用户名或密码错误", http_status=401)
    return user


def build_user_payload(user: SysUser) -> dict:
    roles = [r.code for r in user.roles if r.status == "ACTIVE"]
    permissions: set[str] = set()
    for role in user.roles:
        if role.status != "ACTIVE":
            continue
        for perm in role.permissions:
            permissions.add(perm.code)
    return {
        "id": user.id,
        "org_id": user.org_id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "roles": roles,
        "permissions": sorted(permissions),
    }


async def login(
    db: AsyncSession,
    *,
    username: str,
    password: str,
) -> dict:
    user = await authenticate_user(db, username=username, password=password)
    token, expires_in = create_access_token(
        subject=user.id,
        extra={"org_id": user.org_id, "username": user.username},
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "org_id": user.org_id,
            "roles": [r.code for r in user.roles if r.status == "ACTIVE"],
        },
    }


def me_payload(current: CurrentUser) -> dict:
    return {
        "id": current.id,
        "org_id": current.org_id,
        "username": current.username,
        "nickname": current.nickname,
        "email": current.email,
        "roles": current.roles,
        "permissions": current.permissions,
    }
