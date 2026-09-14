"""Audit log write / query (best-effort writes)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.deps import CurrentUser
from app.core.errors import AppError, get_request_id
from app.core.rbac import is_admin
from app.db.session import AsyncSessionLocal
from app.models.audit import AuditLog
from app.models.base import new_id

logger = logging.getLogger(__name__)


def request_client_meta(request: Request | None) -> dict[str, str | None]:
    if request is None:
        return {"request_id": None, "ip": None, "user_agent": None}
    client = request.client
    return {
        "request_id": get_request_id(request),
        "ip": client.host if client else None,
        "user_agent": (request.headers.get("user-agent") or "")[:512] or None,
    }


def audit_to_dict(row: AuditLog) -> dict[str, Any]:
    return {
        "id": row.id,
        "org_id": row.org_id,
        "user_id": row.user_id,
        "action": row.action,
        "resource_type": row.resource_type,
        "resource_id": row.resource_id,
        "request_id": row.request_id,
        "result": row.result,
        "ip": row.ip,
        "user_agent": row.user_agent,
        "detail": row.detail,
        "created_at": (
            row.created_at.isoformat(sep="T", timespec="milliseconds")
            if row.created_at
            else None
        ),
    }


async def write_audit(
    *,
    action: str,
    result: str,
    org_id: str | None = None,
    user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    request_id: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    detail: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    """Persist one audit row in a separate session; never raise to callers."""
    meta = request_client_meta(request)
    try:
        async with AsyncSessionLocal() as session:
            session.add(
                AuditLog(
                    id=new_id(),
                    org_id=org_id,
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    request_id=request_id or meta["request_id"],
                    result=result,
                    ip=ip or meta["ip"],
                    user_agent=user_agent or meta["user_agent"],
                    detail=detail,
                )
            )
            await session.commit()
    except Exception:
        logger.exception("audit write failed action=%s result=%s", action, result)


async def list_audit_logs(
    db: AsyncSession,
    user: CurrentUser,
    *,
    page: int = 1,
    page_size: int = 20,
    action: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    if not is_admin(user):
        raise AppError(
            "PERMISSION_DENIED",
            "仅管理员可查看审计日志",
            http_status=403,
        )

    filters = [AuditLog.org_id == user.org_id]
    if action and action.strip():
        filters.append(AuditLog.action == action.strip())
    if user_id and user_id.strip():
        filters.append(AuditLog.user_id == user_id.strip())

    base: Select[Any] = select(AuditLog).where(*filters)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    result = await db.execute(
        base.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [audit_to_dict(row) for row in result.scalars().all()]
    return {
        "items": items,
        "total": int(total or 0),
        "page": page,
        "page_size": page_size,
    }
