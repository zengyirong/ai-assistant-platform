"""Conversation + Chat SSE routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ok
from app.core.auth.deps import CurrentUser
from app.core.errors import get_request_id
from app.core.rbac import require_permissions
from app.db.session import get_db
from app.modules.conversation import chat as chat_service
from app.modules.conversation import service as conv_service

conversation_router = APIRouter()
chat_router = APIRouter()


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    kb_ids: list[str] | None = None


class ChatStreamRequest(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=36)
    question: str = Field(min_length=1, max_length=8000)
    kb_ids: list[str] | None = None


@conversation_router.get("")
async def list_conversations(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(require_permissions("conversation:list")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await conv_service.list_conversations(
        db, user, page=page, page_size=page_size
    )
    return ok(request, data)


@conversation_router.post("")
async def create_conversation(
    request: Request,
    body: ConversationCreateRequest,
    user: CurrentUser = Depends(require_permissions("conversation:create")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await conv_service.create_conversation(
        db, user, title=body.title, kb_ids=body.kb_ids
    )
    return ok(request, data)


@conversation_router.get("/{conversation_id}")
async def get_conversation(
    request: Request,
    conversation_id: str,
    user: CurrentUser = Depends(require_permissions("conversation:list")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await conv_service.get_conversation_dict(db, user, conversation_id)
    return ok(request, data)


@conversation_router.delete("/{conversation_id}")
async def delete_conversation(
    request: Request,
    conversation_id: str,
    user: CurrentUser = Depends(require_permissions("conversation:delete")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await conv_service.delete_conversation(db, user, conversation_id)
    return ok(request, {})


@conversation_router.get("/{conversation_id}/messages")
async def list_messages(
    request: Request,
    conversation_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: CurrentUser = Depends(require_permissions("conversation:list")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await conv_service.list_messages(
        db, user, conversation_id, page=page, page_size=page_size
    )
    return ok(request, data)


@chat_router.post("/stream")
async def chat_stream(
    request: Request,
    body: ChatStreamRequest,
    user: CurrentUser = Depends(require_permissions("conversation:create")),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    request_id = get_request_id(request)
    ctx = await chat_service.prepare_stream(
        db,
        user,
        conversation_id=body.conversation_id,
        question=body.question,
        kb_ids=body.kb_ids,
        request_id=request_id,
    )

    async def event_generator():
        try:
            async for line in chat_service.iter_chat_sse(ctx):
                if await request.is_disconnected():
                    await chat_service.mark_aborted(ctx["assistant_message_id"])
                    break
                yield line
        except GeneratorExit:
            await chat_service.mark_aborted(ctx["assistant_message_id"])
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id,
            "X-Accel-Buffering": "no",
        },
    )
