from sqlalchemy.orm import relationship
from magic.utils.db.connection import Base
from sqlalchemy import Column, Integer, String, Text
import time

class Permission(Base):
    """权限模型"""
    __tablename__ = "permission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)
    description = Column(Text, default="")
    category = Column(String(32), default="默认")
    createdAt = Column(Integer, default=0)
    roles = relationship("RolePermission", back_populates="permission", lazy="dynamic")

    def __init__(self, name: str, description: str = "", category: str = "默认"):
        self.name = name
        self.description = description
        self.category = category
        self.createdAt = int(time.time())
