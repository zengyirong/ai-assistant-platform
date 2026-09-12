"""Common API envelope schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiEnvelope(BaseModel, Generic[T]):
    code: str = "OK"
    message: str = "success"
    data: T
    request_id: str


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    request_id: str
    details: Any | None = None


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
