from magic.models.user import User
from magic.utils.db.connection import get_db
from magic.utils.Argon2Password import verifyPassword
from magic.utils.jwt import generateLoginToken
from magic.service.rbac.permissionService import PermissionService
from sqlalchemy import or_
from typing import cast
import time


class UserService:
    @staticmethod
    async def getUserByEmail(email: str) -> User | None:
        return get_db().query(User).filter(User.mail == email).first()
    
    @staticmethod
    async def createUser(name: str, email: str, password: str, ip: str = "") -> User:
        db = get_db()
        new_user = User(
            name=name,
            mail=email,
            password=password,
            url=ip,
            createdAt=int(time.time()),
            lastLogin=0,
            isActive=1,
            isLoggedIn=0
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        PermissionService.assignRoleToUser(new_user.uid, "user")  # pyright: ignore[reportArgumentType]
        
        return new_user
    
    @staticmethod
    async def loginUser(email: str, password: str):
        """
        return:
            - 成功: 返回用户信息字典(包括权限)
            - 失败: 返回错误码
        """
        user = get_db().query(User).filter(or_(User.mail == email)).first()
        if not user:
            return 10101

        isCorrectPassword = verifyPassword(str(user.password), password)

        if isCorrectPassword:
            token = await generateLoginToken(
                cast(int, user.uid),
                cast(str, user.mail)
            )

            permissions = list(user.getAllPermissions())
            
            userInfo = {
                "uid": user.uid,
                "name": user.name,
                "email": user.mail,
                "roles": [ur.role.name for ur in user.userRoles if ur.role],
                "permissions": permissions,
                "token": token
            }

            return userInfo
        else:
            return 10102
    
    @staticmethod
    async def getUsersList():
        """获取用户列表"""
        users = get_db().query(User).all()
        return [
            {
                "uid": user.uid, 
                "name": user.name, 
                "email": user.mail, 
                "roles": [ur.role.name for ur in user.userRoles if ur.role],
                "createdAt": user.createdAt
            } for user in users]
    
    @staticmethod
    async def assignRole(uid: int, roleName: str, currentUserId: int = 0) -> bool:
        """
        为用户分配角色
        
        Parameter:
            uid: 目标用户 UID
            roleName: 角色名称
            currentUserId: 当前操作者的 UID(用于审计)
            
        return:
            bool: 分配成功返回 True
        """
        return PermissionService.assignRoleToUser(uid, roleName, currentUserId)

    @staticmethod
    async def revokeRole(uid: int, roleName: str) -> bool:
        """
        移除用户的角色
        
        参数:
            uid: 目标用户 UID
            roleName: 角色名称
            
        返回:
            bool: 移除成功返回 True
        """
        return PermissionService.removeRoleFromUser(uid, roleName)

    @staticmethod
    async def updateUser(uid: int, data: dict):
        """更新用户信息"""
        db = get_db()
        user = db.query(User).filter(User.uid == uid).first()
        if not user:
            return False
        
        if data.get("username"):
            user.name = data["username"]
        if data.get("email"):
            user.mail = data["email"]
        if data.get("password"):
            user.password = data["password"]
        
        user.updated_at = int(time.time())
        db.commit()
        return True
    
    @staticmethod
    async def deleteUser(uid: int):
        """删除用户"""
        db = get_db()
        user = db.query(User).filter(User.uid == uid).first()
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        return True

    @staticmethod
    async def getUserByUsernameExactly(username: str) -> dict | None:
        """精确查询用户名, 完全匹配"""
        db = get_db()
        user = db.query(User).filter(User.name == username).first()
        if not user:
            return None
        
        return {
            "uid": user.uid, "name": user.name,
            "email": user.mail,
            "createdAt": user.createdAt, "lastLogin": user.lastLogin
        }

    @staticmethod
    async def getUserByUsername(username: str) -> list[dict]:
        """模糊查询用户名, 包含匹配"""
        db = get_db()
        users = db.query(User).filter(User.name.contains(username)).all()
        
        return [{
            "uid": user.uid, "name": user.name,
            "email": user.mail,
            "createdAt": user.createdAt, "lastLogin": user.lastLogin
        } for user in users]

