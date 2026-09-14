"""RAG chat SSE orchestration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import get_llm_client
from app.ai.prompt import build_rag_messages, refuse_message
from app.ai.retrieval import retrieve_chunks, to_citation_dicts
from app.core.auth.deps import CurrentUser
from app.core.config import settings
from app.core.errors import AppError
from app.db.session import AsyncSessionLocal
from app.modules.conversation import service as conv_service
from app.schemas.sse import (
    SseCitationItem,
    make_citation,
    make_done,
    make_error,
    make_start,
    make_text,
)

logger = logging.getLogger(__name__)


async def prepare_stream(
    db: AsyncSession,
    user: CurrentUser,
    *,
    conversation_id: str,
    question: str,
    kb_ids: list[str] | None,
    request_id: str,
) -> dict[str, Any]:
    """Validate + persist USER/ASSISTANT rows before SSE starts."""
    question = question.strip()
    if not question:
        raise AppError("VALIDATION_ERROR", "问题不能为空", http_status=400)

    conversation = await conv_service.get_conversation(db, user, conversation_id)
    resolved_kb_ids = await conv_service.resolve_kb_ids_for_chat(
        db,
        user,
        requested=kb_ids,
        conversation=conversation,
    )
    user_msg, assistant_msg = await conv_service.prepare_chat_messages(
        db,
        conversation=conversation,
        question=question,
        request_id=request_id,
    )
    await db.commit()
    return {
        "conversation_id": conversation.id,
        "user_message_id": user_msg.id,
        "assistant_message_id": assistant_msg.id,
        "org_id": user.org_id,
        "kb_ids": resolved_kb_ids,
        "question": question,
        "request_id": request_id,
    }


async def iter_chat_sse(ctx: dict[str, Any]) -> AsyncIterator[str]:
    """Yield SSE lines for one chat turn. Uses its own DB sessions."""
    request_id = ctx["request_id"]
    conversation_id = ctx["conversation_id"]
    message_id = ctx["assistant_message_id"]
    seq = 0

    def next_seq() -> int:
        nonlocal seq
        seq += 1
        return seq

    yield make_start(
        request_id=request_id,
        conversation_id=conversation_id,
        message_id=message_id,
        seq=next_seq(),
    ).to_sse_line()

    try:
        async with AsyncSessionLocal() as db:
            chunks = await retrieve_chunks(
                db,
                org_id=ctx["org_id"],
                kb_ids=ctx["kb_ids"],
                question=ctx["question"],
            )
            citations = to_citation_dicts(chunks)

        yield make_citation(
            request_id=request_id,
            conversation_id=conversation_id,
            message_id=message_id,
            seq=next_seq(),
            citations=[
                SseCitationItem(
                    document_id=c["document_id"],
                    document_name=c.get("document_name"),
                    chunk_id=c["chunk_id"],
                    page=c.get("page"),
                    section=c.get("section"),
                    score=c.get("score"),
                    snippet=c.get("snippet"),
                )
                for c in citations
            ],
        ).to_sse_line()

        if not chunks:
            text = refuse_message()
            yield make_text(
                request_id=request_id,
                conversation_id=conversation_id,
                message_id=message_id,
                seq=next_seq(),
                content=text,
            ).to_sse_line()
            async with AsyncSessionLocal() as db:
                await conv_service.finalize_assistant_success(
                    db,
                    message_id=message_id,
                    content=text,
                    citations=[],
                )
            yield make_done(
                request_id=request_id,
                conversation_id=conversation_id,
                message_id=message_id,
                seq=next_seq(),
            ).to_sse_line()
            return

        messages = build_rag_messages(question=ctx["question"], chunks=chunks)
        llm = get_llm_client()
        parts: list[str] = []
        async for delta in llm.stream(messages):
            if not delta:
                continue
            parts.append(delta)
            yield make_text(
                request_id=request_id,
                conversation_id=conversation_id,
                message_id=message_id,
                seq=next_seq(),
                content=delta,
            ).to_sse_line()
            # Let the ASGI server flush each SSE frame promptly.
            await asyncio.sleep(0)

        full = "".join(parts).strip() or refuse_message()
        async with AsyncSessionLocal() as db:
            await conv_service.finalize_assistant_success(
                db,
                message_id=message_id,
                content=full,
                citations=citations,
            )
        yield make_done(
            request_id=request_id,
            conversation_id=conversation_id,
            message_id=message_id,
            seq=next_seq(),
        ).to_sse_line()
    except AppError as exc:
        logger.warning("chat stream app error: %s", exc.message)
        async with AsyncSessionLocal() as db:
            await conv_service.finalize_assistant_status(
                db,
                message_id=message_id,
                status="FAILED",
                content=None,
            )
        yield make_error(
            request_id=request_id,
            conversation_id=conversation_id,
            message_id=message_id,
            seq=next_seq(),
            code=exc.code,
            message=exc.message,
        ).to_sse_line()
    except Exception as exc:
        logger.exception("chat stream failed")
        async with AsyncSessionLocal() as db:
            await conv_service.finalize_assistant_status(
                db,
                message_id=message_id,
                status="FAILED",
                content=None,
            )
        yield make_error(
            request_id=request_id,
            conversation_id=conversation_id,
            message_id=message_id,
            seq=next_seq(),
            code="INTERNAL_ERROR",
            message=str(exc) if settings.DEBUG else "服务器内部错误",
        ).to_sse_line()


async def mark_aborted(message_id: str) -> None:
    async with AsyncSessionLocal() as db:
        await conv_service.finalize_assistant_status(
            db,
            message_id=message_id,
            status="ABORTED",
        )
