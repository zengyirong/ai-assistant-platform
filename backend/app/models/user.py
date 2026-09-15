"""RBAC models: user / role / permission."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class SysPermission(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "sys_permission"

    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sys_permission.id", ondelete="SET NULL")
    )
    path: Mapped[str | None] = mapped_column(String(255))
    component: Mapped[str | None] = mapped_column(String(255))
    icon: Mapped[str | None] = mapped_column(String(128))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    visible: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    redirect: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(3),
        nullable=False,
    )


class SysRole(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sys_role"

    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organization.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")

    permissions: Mapped[list[SysPermission]] = relationship(
        secondary="sys_role_permission",
        lazy="selectin",
    )


class SysUser(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sys_user"

    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organization.id"), nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")

    roles: Mapped[list[SysRole]] = relationship(
        secondary="sys_user_role",
        lazy="selectin",
    )


class SysUserRole(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "sys_user_role"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sys_role.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(3),
        nullable=False,
    )


class SysRolePermission(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "sys_role_permission"

    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sys_role.id", ondelete="CASCADE"), nullable=False
    )
    permission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sys_permission.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(3),
        nullable=False,
    )
