"""
Cookie管理工具模块

该模块提供统一的Cookie设置、删除和验证功能, 用于管理用户认证相关的Cookie。
"""

from quart import Response


class CookieManager:
    """Cookie管理器类"""
    
    @staticmethod
    def set_refresh_token(response: Response, refresh_token: str) -> Response:
        """设置刷新令牌Cookie
        
        Args:
            response: Quart响应对象
            refresh_token: 刷新令牌值
            
        Returns:
            Response: 设置好Cookie的响应对象
        """
        response.set_cookie(
            key='lmoadll_refresh_token',
            value=refresh_token,
            httponly=True,            # 防止XSS攻击
            secure=True,              # 仅HTTPS传输
            samesite='None',          # 允许跨站使用
            max_age=30*24*60*60       # 30天过期时间
        )
        return response
    
    @staticmethod
    def set_access_token(response: Response, access_token: str) -> Response:
        """设置访问令牌Cookie
        
        Args:
            response: Quart响应对象
            access_token: 访问令牌值
            
        Returns:
            Response: 设置好Cookie的响应对象
        """
        response.set_cookie(
            key='lmoadllUser',
            value=access_token,
            httponly=True,           # 防止XSS攻击
            secure=True,             # 仅HTTPS传输
            samesite='None',         # 允许跨站使用
            max_age=15*60            # 15分钟过期时间
        )
        return response
    
    @staticmethod
    def delete_refresh_token(response: Response) -> Response:
        """删除刷新令牌Cookie
        
        Args:
            response: Quart响应对象
            
        Returns:
            Response: 删除Cookie后的响应对象
        """
        response.delete_cookie(key='lmoadll_refresh_token')
        return response
    
    @staticmethod
    def delete_access_token(response: Response) -> Response:
        """删除访问令牌Cookie
        
        Args:
            response: Quart响应对象
            
        Returns:
            Response: 删除Cookie后的响应对象
        """
        response.delete_cookie(key='lmoadllUser')
        return response
    
    @staticmethod
    def delete_all_tokens(response: Response) -> Response:
        """删除所有认证相关的Cookie
        
        Args:
            response: Quart响应对象
            
        Returns:
            Response: 删除所有Cookie后的响应对象
        """
        response = CookieManager.delete_refresh_token(response)
        response = CookieManager.delete_access_token(response)
        return response


cookie_manager = CookieManager()