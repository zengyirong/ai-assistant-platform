"""Knowledge base / member / rag_config models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeBase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "knowledge_base"

    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organization.id"), nullable=False, index=True
    )
    space_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("space.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024))
    visibility: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("sys_user.id"), nullable=False, index=True
    )

    members: Mapped[list[KnowledgeBaseMember]] = relationship(
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    rag_config: Mapped[RagConfig | None] = relationship(
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )


class KnowledgeBaseMember(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "knowledge_base_member"

    kb_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_base.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(3),
        nullable=False,
    )

    knowledge_base: Mapped[KnowledgeBase] = relationship(back_populates="members")


class RagConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "rag_config"

    kb_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("knowledge_base.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    chunk_strategy: Mapped[str] = mapped_column(
        String(64), nullable=False, default="recursive"
    )
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False, default=800)
    chunk_overlap: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    score_threshold: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    llm_model: Mapped[str | None] = mapped_column(String(128))
    temperature: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), nullable=False, default=Decimal("0.20")
    )
    system_prompt: Mapped[str | None] = mapped_column(Text)

    knowledge_base: Mapped[KnowledgeBase] = relationship(back_populates="rag_config")
