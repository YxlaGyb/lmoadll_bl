from magic.utils.db.connection import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class User(Base):
    """用户模型"""
    __tablename__ = 'user'
    
    uid = Column(Integer, primary_key=True)
    name = Column(String(32))
    mail = Column(String(150))
    password = Column(String(255))
    url = Column(String(150))
    createdAt = Column(Integer, default=0)
    lastLogin = Column(Integer, default=0)
    isActive = Column(Integer, default=0)
    isLoggedIn = Column(Integer, default=0)

    userRoles = relationship("UserRole", 
        back_populates="user", cascade="all, delete-orphan"
    )

    def getAllPermissions(self):
        """获取用户的所有权限"""
        permissions = set()
        for userRole in self.userRoles:
            role = userRole.role
            if role:
                for rolePerm in role.permissions:
                    if rolePerm.permission:
                        permissions.add(rolePerm.permission.name)
        return permissions
    
    def hasPermission(self, permissionName: str):
        """
        检查用户是否用户指定权限

        Parameter:
            permissionName: 权限名称，如 'user:delete'

        return:
            bool: 如果拥有该权限返回 True, 否则返回 False
        """
        allPerms = self.getAllPermissions()
        return permissionName in allPerms
    
    def hasRole(self, roleName: str):
        """
        检查用户是否拥有指定角色

        Parameter:
            roleName: 角色名称，如 'admin'

        return:
            bool: 如果拥有该角色返回 True, 否则返回 False
        """
        for userRole in self.userRoles:
            if userRole.role and userRole.role.name == roleName:
                return True
        return False
