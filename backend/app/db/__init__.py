"""Import all models here for Alembic metadata discovery."""

from app.db.base import Base

# Phase 1: add model imports, e.g.
# from app.models.user import SysUser  # noqa: F401

__all__ = ["Base"]
