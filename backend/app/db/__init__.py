"""Import all models here for Alembic metadata discovery."""

from app.db.base import Base
from app.models import (  # noqa: F401
    Organization,
    Space,
    SpaceMember,
    SysPermission,
    SysRole,
    SysRolePermission,
    SysUser,
    SysUserRole,
)

__all__ = ["Base"]
