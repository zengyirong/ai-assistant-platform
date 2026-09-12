"""Password hashing and JWT helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.core.errors import AppError


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) > 72:
        raw = raw[:72]
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        raw = plain.encode("utf-8")
        if len(raw) > 72:
            raw = raw[:72]
        return bcrypt.checkpw(raw, hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    *,
    subject: str,
    extra: dict[str, Any] | None = None,
) -> tuple[str, int]:
    expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.APP_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expires_minutes * 60


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.APP_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise AppError(
            "AUTH_UNAUTHORIZED",
            "Token 无效或已过期",
            http_status=401,
        ) from exc
