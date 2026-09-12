"""Organization / Space models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Organization(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organization"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")


class Space(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "space"

    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organization.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512))
    is_default: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    owner_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sys_user.id"))


class SpaceMember(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "space_member"

    space_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("space.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="MEMBER")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(3),
        nullable=False,
    )
