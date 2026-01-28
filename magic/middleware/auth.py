# -*- coding: utf-8 -*-
from quart import request
from functools import wraps
from magic.utils.jwt import verifyJwtPayload
from magic.utils.db.connection import get_db
from magic.models.user import User
from magic.middleware.response import APIException


async def getCurrentUser():
    """
    获取当前用户信息

    从 Token 中获取用户UID, 然后从数据库中加载完整的用户对象, 包括角色和权限

    return:
        User: 如果用户已登录, 返回用户对象; 否则返回 None
    """
    token = request.cookies.get('forestwhisper')
    if not token:
        return None
    payload = await verifyJwtPayload(token)
    if not payload:
        return None
    
    db = get_db()
    user = db.query(User).filter(User.uid == payload.uid).first()
    return user

def AuthMiddleware(requiredPermission: str | None = None):
    """
    身份验证中间件装饰器

    如果指定了 requiredPermission, 则同时检查权限

    Parameter:
        requiredPermission: 可选, 需要的权限名称(如 "user:delete")
    
    示例:
        ```
        @bp.route('/admin')
        @AuthMiddleware('system:config')
        async def admin_page():
            return 'Admin page'
        ```
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = await getCurrentUser()
            if not user:
                raise APIException("未登录或登录已过期喵喵", code=401)
            payload = await verifyJwtPayload(request.cookies.get("forestwhisper"))
            if not payload or payload.iss != "lmoadll" or payload.aud != "lmoadll":
                raise APIException("Token无效喵喵", code=401)
            
            if requiredPermission:
                if not user.hasPermission(requiredPermission):
                    raise APIException(f"没有 '{requiredPermission}' 权限喵", code=403)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def RequireRole(*roleNames):
    """
    角色要求装饰器
    这个装饰器用于检查用户是否拥有指定角色中的任何一个

    Parameter:
        *roleNames: 可变参数, 角色名称列表

    示例:
        ```
        @bp.route('/admin')
        @RequireRole('admin', 'super_admin')
        async def admin_page():
            return 'Admin page'
        ```
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = await getCurrentUser()
            
            if not user:
                raise APIException("未登录或登录已过期喵喵", code=401)
            
            has_role = any(user.hasRole(role) for role in roleNames)
            if not has_role:
                role_list = ', '.join(roleNames)
                raise APIException(f"没有拥有角色: {role_list} 喵", code=403)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
