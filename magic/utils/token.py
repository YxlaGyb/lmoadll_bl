# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
JWT Token 管理模块

该模块提供JWT token的创建、验证和管理功能,
用于应用程序的用户认证和会话管理。
"""

import secrets
import logging
import jwt as pyjwt
from quart import Quart, request
from typing import Dict
from datetime import datetime, timezone, timedelta
from magic.middleware.errorhandler import handle_errors
from quart_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    verify_jwt_in_request,
    decode_token
)



__all__ = [
    'InitJwtManager',
    'CreateTokens',
    'CreateJwtToken',
    'RefreshToken',
    'GetCurrentUserIdentity'
]


def get_utc_now():
    """安全获取当前UTC时间"""
    return datetime.now(timezone.utc)


class JWTKeyManager:
    def __init__(self, rotation_days: int = 7, max_keys: int = 10):
        self.rotation_days = rotation_days
        self.max_keys = max_keys
        self.key_dict: Dict[str, datetime] = {} # {'6e969ed020840444240ab4c440fdb87d7b557bc070ea3a837d59345351075794': datetime.datetime(2025, 10, 22, 2, 55, 45, 225830, tzinfo=datetime.timezone.utc)}
        self._add_new_key()
    
    def _add_new_key(self) -> str:
        """添加新密钥到字典"""
        new_key = secrets.token_hex(32)
        self.key_dict[new_key] = get_utc_now()
        return new_key
    
    def _clean_old_keys(self):
        """清理过期密钥"""
        current_time = get_utc_now()
        expired_keys: list[str] = []
        for key, created_time in self.key_dict.items():
            key_age = current_time - created_time
            if key_age.days > self.rotation_days:
                expired_keys.append(key)

        for key in expired_keys:
            del self.key_dict[key]
    
    def get_current_key(self) -> str:
        """获取当前有效密钥"""
        self._clean_old_keys()
        
        if not self.key_dict:
            return self._add_new_key()
        
        latest_key = max(self.key_dict.items(), key=lambda x: x[1])[0]
        return latest_key
    
    def get_all_valid_keys(self) -> list[str]:
        """获取所有有效密钥"""
        self._clean_old_keys()
        return list(self.key_dict.keys())


jwt_key_manager = JWTKeyManager(rotation_days=7, max_keys=8)


@handle_errors("初始化JWT管理器失败")
def InitJwtManager(app: Quart) -> JWTManager:
    """初始化JWT管理器, 初始化JWT管理器并配置JWT相关设置"""

    if not app.config.get('JWT_SECRET_KEY'):
        app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)
    
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    jwt = JWTManager(app)
    
    @jwt.encode_key_loader
    def encode_key_callback(identity):
        """编码时使用当前最新密钥"""
        return jwt_key_manager.get_current_key()
    
    @jwt.decode_key_loader
    def decode_key_callback(header, payload):
        """
        解码时智能选择密钥, 获取所有有效密钥, 如果有令牌, 尝试自动选择正确的密钥（单token模式）
        """
        valid_keys = jwt_key_manager.get_all_valid_keys()
        
        auth_header = request.headers.get('Authorization', '')
        # 单token模式：只使用lmoadll_refresh_token作为唯一token
        cookie_token = request.cookies.get('lmoadll_refresh_token')
        
        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # 去掉 "Bearer " 前缀
        elif cookie_token:
            token = cookie_token
        
        if token:
            for key in valid_keys:
                try:
                    pyjwt.decode(token, key, algorithms=["HS256"], options={"verify_exp": False})
                    return key
                except pyjwt.InvalidTokenError:
                    continue
        return jwt_key_manager.get_current_key() # 如果没有令牌或者所有密钥都失败，返回当前密钥(让库自己处理错误)
    
    return jwt


def CreateTokens(identity, additional_claims=None):
    """创建双令牌, 同时生成Access Token和Refresh Token
    
    Args:
        identity: 用户身份信息
        additional_claims: 额外的声明信息
    
    Returns:
        dict: 包含access_token和refresh_token的字典
    """
    try:
        # 设置默认的额外声明
        if additional_claims is None:
            additional_claims = {}
        
        # 为access token添加特定声明
        access_claims = additional_claims.copy()
        access_claims.update({
            'token_type': 'access',
            'created_at': get_utc_now().isoformat()
        })
        
        # 为refresh token添加特定声明
        refresh_claims = additional_claims.copy()
        refresh_claims.update({
            'token_type': 'refresh',
            'created_at': get_utc_now().isoformat()
        })
        
        # 创建访问令牌和刷新令牌
        access_token = create_access_token(
            identity=identity, 
            additional_claims=access_claims
        )
        
        refresh_token = create_refresh_token(
            identity=identity, 
            additional_claims=refresh_claims
        )
        
        return {
            'lmoadllUser': access_token,
            'lmoadll_refresh_token': refresh_token
        }
    except Exception as e:
        logging.error(f"创建JWT令牌失败喵: {e}")
        return None


def CreateJwtToken(identity, additional_claims=None):
    """创建访问令牌, 根据用户身份创建JWT访问令牌(向后兼容)"""
    try:
        # 调用新的双令牌创建函数，但只返回access token
        tokens = CreateTokens(identity, additional_claims)
        if tokens:
            return tokens['lmoadllUser']
        return None
    except Exception as e:
        logging.error(f"创建JWT令牌失败喵: {e}")
        return None


def RefreshToken(lmoadll_refresh_token, request=None):
    """
    刷新访问令牌, 使用Refresh Token获取新的Access Token
    
    Args:
        refresh_token: 有效的Refresh Token
        request: Quart请求对象,用于进行额外的安全验证
    
    Returns:
        str: 新的Access Token, 如果刷新失败则返回None

    解码refresh token以获取用户身份, 验证是否为refresh token类型, 获取用户身份, 创建新的access token
    """
    try:
        decoded_token = decode_token(lmoadll_refresh_token)
        
        # 安全改进：增强验证逻辑
        # 1. 验证token类型
        if decoded_token.get('token_type') != 'refresh':
            return None
        
        # 2. 验证用户身份存在
        identity = decoded_token.get('sub')
        if not identity:
            return None
        
        # 3. 如果提供了请求对象，进行额外的安全检查
        if request:
            # [ ] TODO 需要额外的安全检查，例如验证来源IP等
            # 验证来源IP（可选，如果需要严格的会话绑定）
            # 注意：在实际生产环境中，需要考虑代理和CDN的情况
            current_ip = request.remote_addr  # noqa: F841
            # 可以在token中添加更多的上下文信息进行验证
            
            # 验证用户代理
            current_user_agent = request.headers.get('User-Agent', '')  # noqa: F841
            # 可以在创建token时存储这些信息，然后在这里进行验证
            
            # 检查请求频率（可以集成到Redis等缓存中）
            # 这里可以添加请求限流逻辑，防止暴力刷新攻击
        
        # 4. 验证token是否在黑名单中（预留接口，需要实现黑名单功能）
        # 此处可以调用检查token是否被撤销的函数
        
        # 5. 创建新的access token
        access_claims = {
            'token_type': 'access',
            'created_at': get_utc_now().isoformat()
        }
        
        new_access_token = create_access_token(
            identity=identity, 
            additional_claims=access_claims
        )
        
        return new_access_token
    except Exception as e:
        logging.error(f"刷新令牌失败喵: {e}")
        return None


def GetCurrentUserIdentity():
    """
    获取当前用户UID, 支持Cookie和Header两种方式

    1. 首先尝试标准的JWT验证(从Authorization头获取)
    2. 如果标准方式失败, 尝试从cookie中获取令牌
    """
    try:
        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            if identity is not None:
                return identity
        except Exception as e:
            logging.error(f"Header验证失败喵: {e}")
            # Header验证失败，继续尝试cookie方式
            pass
        
        # 单token模式：只使用lmoadll_refresh_token作为唯一token
        token = request.cookies.get('lmoadll_refresh_token')
        if token:
            try:
                decoded_token = decode_token(token)
                # 验证token类型为refresh（单token模式下的唯一token）
                if decoded_token.get('token_type') == 'refresh':
                    identity = decoded_token.get('sub')
                    if identity:
                        return identity
                    
            except Exception as e:
                logging.error(f"Cookie解码失败喵: {e}")
                # 解码cookie令牌失败，继续
                pass
        
        # 所有方式都失败，返回None
        return None
        
    except Exception as e:
        logging.error(f"获取用户身份失败喵: {e}")
        return None
