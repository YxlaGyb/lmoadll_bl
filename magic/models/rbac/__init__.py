"""RBAC 模型包"""

from magic.models.rbac.role import Role
from magic.models.rbac.permissions import Permission
from magic.models.rbac.userRoles import UserRole
from magic.models.rbac.rolePermissions import RolePermission

__all__ = [
    "Role",
    "Permission",
    "UserRole",
    "RolePermission"
]
