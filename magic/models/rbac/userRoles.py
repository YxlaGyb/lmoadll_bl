from sqlalchemy.orm import relationship
from magic.utils.db.connection import Base
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
import time

class UserRole(Base):
    """用户角色关联模型"""
    __tablename__ = "userrole"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey("user.uid", ondelete="CASCADE"), nullable=False)
    roleId = Column(Integer, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)
    grantedAt = Column(Integer, default=0)
    grantedBy = Column(Integer, default=0)

    user = relationship("User", back_populates="userRoles")
    role = relationship("Role", back_populates="users")

    __table_args__ = (
        UniqueConstraint("userId", "roleId", name="uixUserRole"),
    )

    def __init__(self, userId: int, roleId: int, grantedBy: int = 0):
        self.userId = userId
        self.roleId = roleId
        self.grantedAt = int(time.time())
        self.grantedBy = grantedBy
