from magic.utils.db.connection import get_db
from magic.models.rbac import Role, Permission, UserRole, RolePermission
from magic.models.user import User
from typing import List

class PermissionService:
    """
    权限服务类, 封装权限相关的业务逻辑
    
    这个服务类提供了权限管理的核心功能，
    包括权限的创建、角色管理、权限分配等。
    """

    @staticmethod
    def getOrCreateRole(roleName: str, description: str = '') -> Role:
        """
        获取或创建角色
        
        Parameter:
            roleName: 角色名称
            description: 角色描述
            
        return:
            Role: 已存在或新创建的角色对象
        """
        db = get_db()
        role = db.query(Role).filter_by(name=roleName).first()
        if not role:
            role = Role(name=roleName, description=description)
            db.add(role)
            db.commit()
            db.refresh(role)
        return role

    @staticmethod
    def getOrCreatePermission(permissionName: str, description: str = '', category: str = '默认') -> Permission:
        """
        获取或创建权限
        
        Parameter:
            permissionName: 权限名称(格式：资源:操作)
            description: 权限描述
            category: 权限分类
            
        return:
            Permission: 已存在或新创建的权限对象
        """
        db = get_db()
        perm = db.query(Permission).filter_by(name=permissionName).first()
        if not perm:
            perm = Permission(name=permissionName, description=description, category=category)
            db.add(perm)
            db.commit()
            db.refresh(perm)
        return perm

    @staticmethod
    def assignRoleToUser(userId: int, roleName: str, grantedBy: int = 0) -> bool:
        """
        为用户分配角色
        
        Parameter:
            userId: 用户的 UID
            roleName: 要分配的角色名称
            grantedBy: 分配角色的管理员 UID
            
        return:
            bool: 分配成功返回 True, 如果已拥有该角色也返回 True
        """
        db = get_db()
        user = db.query(User).filter_by(uid=userId).first()
        if not user:
            return False
        
        role = db.query(Role).filter_by(name=roleName).first()
        if not role:
            return False
        
        existing = db.query(UserRole).filter_by(
            userId=userId, roleId=role.id
        ).first()
        
        if existing:
            return True
        
        userRole = UserRole(userId=userId, roleId=role.id, grantedBy=grantedBy)  # pyright: ignore[reportArgumentType]
        db.add(userRole)
        db.commit()
        return True
    
    @staticmethod
    def removeRoleFromUser(userId: int, roleName: str) -> bool:
        """
        移除用户的角色
        
        Parameter:
            userId: 用户的 UID
            roleName: 要移除的角色名称
            
        return:
            bool: 移除成功返回 True, 用户或角色不存在返回 False
        """
        db = get_db()
        user = db.query(User).filter_by(uid=userId).first()
        if not user:
            return False
        
        role = db.query(Role).filter_by(name=roleName).first()
        if not role:
            return False
        
        userRole = db.query(UserRole).filter_by(
            userId=userId, roleId=role.id
        ).first()
        
        if userRole:
            db.delete(userRole)
            db.commit()
        
        return True

    @staticmethod
    def grantPermissionToRole(roleName: str, permissionName: str) -> bool:
        """
        为角色授予权限
        
        Parameter:
            roleName: 角色名称
            permissionName: 权限名称
            
        return:
            bool: 授予成功返回 True
        """
        db = get_db()
        role = db.query(Role).filter_by(name=roleName).first()
        if not role:
            return False
        
        permission = db.query(Permission).filter_by(name=permissionName).first()
        if not permission:
            return False
        
        existing = db.query(RolePermission).filter_by(
            roleId=role.id,
            permissionId=permission.id
        ).first()
        
        if existing:
            return True
        
        rolePerm = RolePermission(roleId=role.id, permissionId=permission.id)  # pyright: ignore[reportArgumentType]
        db.add(rolePerm)
        db.commit()
        return True

    @staticmethod
    def revokePermissionFromRole(roleName: str, permissionName: str) -> bool:
        """
        移除角色的权限
        
        Parameter:
            roleName: 角色名称
            permissionName: 权限名称
            
        return:
            bool: 移除成功返回 True
        """
        db = get_db()
        role = db.query(Role).filter_by(name=roleName).first()
        if not role:
            return False
        
        permission = db.query(Permission).filter_by(name=permissionName).first()
        if not permission:
            return False
        
        rolePerm = db.query(RolePermission).filter_by(
            roleId=role.id,
            permissionId=permission.id
        ).first()
        
        if rolePerm:
            db.delete(rolePerm)
            db.commit()
        
        return True
    
    @staticmethod
    def getUserPermissions(userId: int) -> List[str]:
        """
        获取用户的所有权限名称
        
        Parameter:
            userId: 用户的 UID
            
        return:
            List[str]: 权限名称列表
        """
        db = get_db()
        user = db.query(User).filter_by(uid=userId).first()
        if not user:
            return []
        
        return list(user.getAllPermissions())

    @staticmethod
    def checkUserPermission(userId: int, permissionName: str) -> bool:
        """
        检查用户是否拥有指定权限
        
        Parameter:
            userId: 用户的 UID
            permissionName: 要检查的权限名称
            
        return:
            bool: 拥有该权限返回 True, 否则返回 False
        """
        db = get_db()
        user = db.query(User).filter_by(uid=userId).first()
        if not user:
            return False
        
        return user.hasPermission(permissionName)
