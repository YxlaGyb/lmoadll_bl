from magic.utils.db.connection import Base
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

class RolePermission(Base):
    __tablename__ = "rolePermission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    roleId = Column(Integer, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)
    permissionId = Column(Integer, ForeignKey("permission.id", ondelete="CASCADE"), nullable=False)

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")

    __table_args__ = (
        UniqueConstraint("roleId", "permissionId", name="uixRolePermission"),
    )

    def __init__(self, roleId: int, permissionId: int):
        self.roleId = roleId
        self.permissionId = permissionId
