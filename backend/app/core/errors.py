"""Unified API error codes and exception handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        http_status: int = 400,
        details: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details
        super().__init__(message)


# Keep in sync with docs/api.md Error Matrix
ERROR_HTTP_STATUS: dict[str, int] = {
    "VALIDATION_ERROR": 400,
    "AUTH_UNAUTHORIZED": 401,
    "PERMISSION_DENIED": 403,
    "KB_PERMISSION_DENIED": 403,
    "KB_NOT_FOUND": 404,
    "DOCUMENT_NOT_FOUND": 404,
    "SPACE_NOT_FOUND": 404,
    "CONVERSATION_NOT_FOUND": 404,
    "DOCUMENT_DUPLICATED": 409,
    "SPACE_NAME_CONFLICT": 409,
    "USER_NAME_CONFLICT": 409,
    "ROLE_CODE_CONFLICT": 409,
    "PERMISSION_CODE_CONFLICT": 409,
    "USER_NOT_FOUND": 404,
    "ROLE_NOT_FOUND": 404,
    "PERMISSION_NOT_FOUND": 404,
    "DOCUMENT_FORMAT_INVALID": 422,
    "DOCUMENT_TOO_LARGE": 422,
    "DOCUMENT_PARSE_FAILED": 422,
    "LLM_RATE_LIMIT": 429,
    "VECTOR_STORE_UNAVAILABLE": 503,
    "SERVICE_UNAVAILABLE": 503,
    "LLM_TIMEOUT": 504,
    "INTERNAL_ERROR": 500,
}


def error_body(
    *,
    code: str,
    message: str,
    request_id: str,
    details: Any = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "code": code,
        "message": message,
        "request_id": request_id,
    }
    if details is not None:
        body["details"] = details
    return body


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or request.headers.get(
        "X-Request-ID", "req_unknown"
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=error_body(
                code=exc.code,
                message=exc.message,
                request_id=get_request_id(request),
                details=exc.details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=error_body(
                code="VALIDATION_ERROR",
                message="参数校验失败",
                request_id=get_request_id(request),
                details=exc.errors(),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "AUTH_UNAUTHORIZED" if exc.status_code == 401 else "INTERNAL_ERROR"
        if exc.status_code == 403:
            code = "PERMISSION_DENIED"
        elif exc.status_code == 404:
            code = "KB_NOT_FOUND"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                code=code,
                message=str(exc.detail),
                request_id=get_request_id(request),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=error_body(
                code="INTERNAL_ERROR",
                message="服务器内部错误",
                request_id=get_request_id(request),
                details=str(exc) if settings_debug() else None,
            ),
        )


def settings_debug() -> bool:
    from app.core.config import settings

    return settings.DEBUG
