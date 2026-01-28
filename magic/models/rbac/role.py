from magic.utils.db.connection import Base
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
import time

class Role(Base):
    """角色模型"""
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), unique=True, nullable=False)
    description = Column(Text, default="")
    createdAt = Column(Integer, default=0)
    updatedAt = Column(Integer, default=0)
    permissions = relationship("RolePermission", back_populates="role", lazy="dynamic")
    users = relationship("UserRole", back_populates="role", lazy="dynamic")

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.createdAt = int(time.time())
        self.updatedAt = int(time.time())
