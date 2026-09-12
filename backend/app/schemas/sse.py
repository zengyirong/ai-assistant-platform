"""SSE Protocol V1 Pydantic models — see docs/sse-protocol.md."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

SseEventName = Literal["start", "text", "citation", "done", "error"]


class SseCitationItem(BaseModel):
    document_id: str
    document_name: str | None = None
    chunk_id: str
    page: int | None = None
    section: str | None = None
    score: float | None = None
    snippet: str | None = None


class SseEnvelope(BaseModel):
    version: Literal["1.0"] = "1.0"
    event: SseEventName
    request_id: str
    conversation_id: str
    message_id: str
    seq: int = Field(ge=1)
    data: dict[str, Any] = Field(default_factory=dict)

    def to_sse_line(self) -> str:
        return f"data: {self.model_dump_json()}\n\n"


def make_start(
    *,
    request_id: str,
    conversation_id: str,
    message_id: str,
    seq: int = 1,
) -> SseEnvelope:
    return SseEnvelope(
        event="start",
        request_id=request_id,
        conversation_id=conversation_id,
        message_id=message_id,
        seq=seq,
        data={"status": "GENERATING"},
    )


def make_text(
    *,
    request_id: str,
    conversation_id: str,
    message_id: str,
    seq: int,
    content: str,
) -> SseEnvelope:
    return SseEnvelope(
        event="text",
        request_id=request_id,
        conversation_id=conversation_id,
        message_id=message_id,
        seq=seq,
        data={"content": content},
    )


def make_citation(
    *,
    request_id: str,
    conversation_id: str,
    message_id: str,
    seq: int,
    citations: list[SseCitationItem],
) -> SseEnvelope:
    return SseEnvelope(
        event="citation",
        request_id=request_id,
        conversation_id=conversation_id,
        message_id=message_id,
        seq=seq,
        data={"citations": [c.model_dump() for c in citations]},
    )


def make_done(
    *,
    request_id: str,
    conversation_id: str,
    message_id: str,
    seq: int,
    finish_reason: str = "stop",
) -> SseEnvelope:
    return SseEnvelope(
        event="done",
        request_id=request_id,
        conversation_id=conversation_id,
        message_id=message_id,
        seq=seq,
        data={"status": "COMPLETED", "finish_reason": finish_reason},
    )


def make_error(
    *,
    request_id: str,
    conversation_id: str,
    message_id: str,
    seq: int,
    code: str,
    message: str,
) -> SseEnvelope:
    return SseEnvelope(
        event="error",
        request_id=request_id,
        conversation_id=conversation_id,
        message_id=message_id,
        seq=seq,
        data={"code": code, "message": message},
    )
