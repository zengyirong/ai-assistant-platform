"""Conversation application service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth.deps import CurrentUser
from app.core.errors import AppError
from app.models.conversation import Conversation, ConversationMessage, MessageCitation
from app.models.document import Document
from app.modules.knowledge import service as kb_service


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat(sep="T", timespec="milliseconds") if dt else None


def conversation_to_dict(conv: Conversation) -> dict[str, Any]:
    return {
        "id": conv.id,
        "org_id": conv.org_id,
        "user_id": conv.user_id,
        "title": conv.title,
        "kb_scope": conv.kb_scope,
        "created_at": _iso(conv.created_at),
        "updated_at": _iso(conv.updated_at),
    }


def citation_to_dict(c: MessageCitation, *, document_name: str | None = None) -> dict[str, Any]:
    return {
        "document_id": c.document_id,
        "document_name": document_name,
        "chunk_id": c.chunk_id,
        "page": c.page,
        "section": c.section,
        "score": float(c.score) if c.score is not None else None,
        "snippet": c.snippet,
        "sort_order": c.sort_order,
    }


def message_to_dict(
    msg: ConversationMessage,
    *,
    document_names: dict[str, str] | None = None,
) -> dict[str, Any]:
    names = document_names or {}
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "role": msg.role,
        "content": msg.content,
        "status": msg.status,
        "request_id": msg.request_id,
        "citations": [
            citation_to_dict(c, document_name=names.get(c.document_id))
            for c in (msg.citations or [])
        ],
        "created_at": _iso(msg.created_at),
    }


async def create_conversation(
    db: AsyncSession,
    user: CurrentUser,
    *,
    title: str | None = None,
    kb_ids: list[str] | None = None,
) -> dict[str, Any]:
    scope = kb_ids or []
    for kb_id in scope:
        await kb_service.ensure_kb_access(db, user, kb_id, needed="VIEW")
    conv = Conversation(
        org_id=user.org_id,
        user_id=user.id,
        title=title or "新会话",
        kb_scope=scope or None,
    )
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return conversation_to_dict(conv)


async def list_conversations(
    db: AsyncSession,
    user: CurrentUser,
    *,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    filters = [
        Conversation.org_id == user.org_id,
        Conversation.user_id == user.id,
    ]
    base: Select[Any] = select(Conversation).where(*filters)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    result = await db.execute(
        base.order_by(Conversation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [conversation_to_dict(c) for c in result.scalars().all()]
    return {
        "items": items,
        "total": int(total or 0),
        "page": page,
        "page_size": page_size,
    }


async def get_conversation(
    db: AsyncSession,
    user: CurrentUser,
    conversation_id: str,
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv is None or conv.org_id != user.org_id or conv.user_id != user.id:
        raise AppError("CONVERSATION_NOT_FOUND", "会话不存在", http_status=404)
    return conv


async def get_conversation_dict(
    db: AsyncSession,
    user: CurrentUser,
    conversation_id: str,
) -> dict[str, Any]:
    conv = await get_conversation(db, user, conversation_id)
    return conversation_to_dict(conv)


async def delete_conversation(
    db: AsyncSession,
    user: CurrentUser,
    conversation_id: str,
) -> None:
    conv = await get_conversation(db, user, conversation_id)
    await db.delete(conv)
    await db.flush()


async def list_messages(
    db: AsyncSession,
    user: CurrentUser,
    conversation_id: str,
    *,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    await get_conversation(db, user, conversation_id)
    base: Select[Any] = select(ConversationMessage).where(
        ConversationMessage.conversation_id == conversation_id
    )
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    result = await db.execute(
        base.order_by(ConversationMessage.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .options(selectinload(ConversationMessage.citations))
    )
    messages = list(result.scalars().all())
    doc_ids = {
        c.document_id
        for m in messages
        for c in (m.citations or [])
        if c.document_id
    }
    document_names: dict[str, str] = {}
    if doc_ids:
        name_rows = await db.execute(
            select(Document.id, Document.file_name).where(Document.id.in_(doc_ids))
        )
        document_names = {row[0]: row[1] for row in name_rows.all() if row[1]}
    items = [
        message_to_dict(m, document_names=document_names) for m in messages
    ]
    return {
        "items": items,
        "total": int(total or 0),
        "page": page,
        "page_size": page_size,
    }


async def resolve_kb_ids_for_chat(
    db: AsyncSession,
    user: CurrentUser,
    *,
    requested: list[str] | None,
    conversation: Conversation,
) -> list[str]:
    if requested:
        kb_ids = requested
    elif conversation.kb_scope:
        kb_ids = list(conversation.kb_scope)
    else:
        kb_ids = await kb_service.list_accessible_kb_ids(db, user)

    if not kb_ids:
        raise AppError(
            "VALIDATION_ERROR",
            "没有可检索的知识库",
            http_status=400,
        )

    for kb_id in kb_ids:
        await kb_service.ensure_kb_access(db, user, kb_id, needed="VIEW")
    return kb_ids


async def prepare_chat_messages(
    db: AsyncSession,
    *,
    conversation: Conversation,
    question: str,
    request_id: str,
) -> tuple[ConversationMessage, ConversationMessage]:
    user_msg = ConversationMessage(
        conversation_id=conversation.id,
        role="USER",
        content=question,
        status="COMPLETED",
        request_id=request_id,
    )
    assistant_msg = ConversationMessage(
        conversation_id=conversation.id,
        role="ASSISTANT",
        content=None,
        status="GENERATING",
        request_id=request_id,
    )
    db.add(user_msg)
    db.add(assistant_msg)
    if not conversation.title or conversation.title == "新会话":
        conversation.title = question.strip()[:40] or "新会话"
    await db.flush()
    return user_msg, assistant_msg


async def finalize_assistant_success(
    db: AsyncSession,
    *,
    message_id: str,
    content: str,
    citations: list[dict[str, Any]],
) -> None:
    result = await db.execute(
        select(ConversationMessage).where(ConversationMessage.id == message_id)
    )
    msg = result.scalar_one_or_none()
    if msg is None:
        return
    msg.content = content
    msg.status = "COMPLETED"
    for item in citations:
        db.add(
            MessageCitation(
                message_id=msg.id,
                document_id=item["document_id"],
                chunk_id=item["chunk_id"],
                page=item.get("page"),
                section=item.get("section"),
                score=(
                    Decimal(str(item["score"]))
                    if item.get("score") is not None
                    else None
                ),
                snippet=(item.get("snippet") or "")[:1024] or None,
                sort_order=int(item.get("sort_order") or 0),
            )
        )
    await db.commit()


async def finalize_assistant_status(
    db: AsyncSession,
    *,
    message_id: str,
    status: str,
    content: str | None = None,
) -> None:
    result = await db.execute(
        select(ConversationMessage).where(ConversationMessage.id == message_id)
    )
    msg = result.scalar_one_or_none()
    if msg is None:
        return
    if msg.status in {"COMPLETED", "ABORTED", "FAILED"}:
        return
    msg.status = status
    if content is not None:
        msg.content = content
    await db.commit()
