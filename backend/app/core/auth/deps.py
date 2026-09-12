"""Auth FastAPI dependencies."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import SysRole, SysUser

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: str
    org_id: str
    username: str
    nickname: str | None
    email: str | None
    roles: list[str]
    permissions: list[str]


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            "AUTH_UNAUTHORIZED",
            "未登录或 Token 缺失",
            http_status=401,
        )

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise AppError("AUTH_UNAUTHORIZED", "Token 无效", http_status=401)

    stmt = (
        select(SysUser)
        .where(SysUser.id == user_id)
        .options(
            selectinload(SysUser.roles).selectinload(SysRole.permissions),
        )
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None or user.status != "ACTIVE":
        raise AppError("AUTH_UNAUTHORIZED", "用户不存在或已禁用", http_status=401)

    roles = [r.code for r in user.roles if r.status == "ACTIVE"]
    permissions: set[str] = set()
    for role in user.roles:
        if role.status != "ACTIVE":
            continue
        for perm in role.permissions:
            permissions.add(perm.code)

    current = CurrentUser(
        id=user.id,
        org_id=user.org_id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        roles=roles,
        permissions=sorted(permissions),
    )
    request.state.current_user = current
    return current
