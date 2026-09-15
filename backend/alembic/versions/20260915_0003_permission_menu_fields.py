"""Extend sys_permission with menu metadata columns.

Revision ID: 20260915_0003
Revises: 20260914_0002
Create Date: 2026-09-15

Supports RBAC menu tree (type=MENU) without a separate sys_menu table.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260915_0003"
down_revision: str | None = "20260914_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sys_permission",
        sa.Column("path", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sys_permission",
        sa.Column("component", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sys_permission",
        sa.Column("icon", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "sys_permission",
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "sys_permission",
        sa.Column(
            "visible",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "sys_permission",
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="ACTIVE",
        ),
    )
    op.add_column(
        "sys_permission",
        sa.Column("redirect", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sys_permission", "redirect")
    op.drop_column("sys_permission", "status")
    op.drop_column("sys_permission", "visible")
    op.drop_column("sys_permission", "sort_order")
    op.drop_column("sys_permission", "icon")
    op.drop_column("sys_permission", "component")
    op.drop_column("sys_permission", "path")
