"""RBAC FastAPI dependencies."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends

from app.core.auth.deps import CurrentUser, get_current_user
from app.core.errors import AppError


def require_permissions(*codes: str) -> Callable[..., CurrentUser]:
    async def _dependency(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        missing = [code for code in codes if code not in user.permissions]
        if missing:
            raise AppError(
                "PERMISSION_DENIED",
                f"缺少权限: {', '.join(missing)}",
                http_status=403,
            )
        return user

    return _dependency


def is_admin(user: CurrentUser) -> bool:
    return "ADMIN" in user.roles
