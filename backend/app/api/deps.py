"""API response helpers."""

from __future__ import annotations

from typing import Any

from fastapi import Request


def ok(request: Request, data: Any = None) -> dict[str, Any]:
    return {
        "code": "OK",
        "message": "success",
        "data": {} if data is None else data,
        "request_id": getattr(request.state, "request_id", "req_unknown"),
    }
