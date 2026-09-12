"""Conversation / message / citation models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.mysql import JSON, MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversation"

    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organization.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sys_user.id"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(255))
    kb_scope: Mapped[list | None] = mapped_column(JSON)

    messages: Mapped[list[ConversationMessage]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ConversationMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversation_message"

    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str | None] = mapped_column(MEDIUMTEXT)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(36), index=True)
    token_input: Mapped[int | None] = mapped_column(Integer)
    token_output: Mapped[int | None] = mapped_column(Integer)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    citations: Mapped[list[MessageCitation]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="MessageCitation.sort_order",
    )


class MessageCitation(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "message_citation"

    message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation_message.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document.id"), nullable=False
    )
    chunk_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document_chunk.id"), nullable=False
    )
    page: Mapped[int | None] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(String(255))
    score: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    snippet: Mapped[str | None] = mapped_column(String(1024))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(3),
        nullable=False,
    )

    message: Mapped[ConversationMessage] = relationship(back_populates="citations")
