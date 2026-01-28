# -*- coding: utf-8 -*-
import jwt as pyjwt
import secrets
import time
from dataclasses import dataclass, asdict
from magic.utils.log3 import logger
from typing import Optional, Dict, Set, List, Tuple


JWT_ISS = "lmoadll"
JWT_AUD = "lmoadll"

@dataclass
class Payload:
    jid: str
    uid: int
    email: str
    expired: int
    create: int
    iss: str = JWT_ISS
    aud: str = JWT_AUD


class KeyManager:
    _mem_keys: Dict[str, str] = {}
    _rotation_interval = 7 * 24 * 3600

    @classmethod
    async def getKeyForSigning(cls) -> tuple[str, str]:
        """获取用于签名的密钥"""
        now = int(time.time())
        if not cls._mem_keys or (now - int(max(cls._mem_keys.keys()))) > cls._rotation_interval:
            cls._mem_keys[str(now)] = secrets.token_urlsafe(32)
        latestKid = max(cls._mem_keys.keys())
        return latestKid, cls._mem_keys[latestKid]

    @classmethod
    async def getKeyForVerifying(cls, kid: str) -> Optional[str]:
        """根据kid获取用于验证的密钥"""
        return cls._mem_keys.get(kid)


class TokenManager:
    _userTokens: Dict[str, List[Tuple[str, int]]] = {}  # email -> list of (jid, expired_timestamp)
    _blacklist: Set[str] = set()

    @classmethod
    async def addToken(cls, email: str, jid: str, expiredTimestamp: int):
        if email not in cls._userTokens:
            cls._userTokens[email] = []
        cls._userTokens[email].append((jid, expiredTimestamp))

    @classmethod
    async def revokeTokenById(cls, jid: str):
        """撤销单个token"""
        cls._blacklist.add(jid)

    @classmethod
    async def revokeTokensByUser(cls, email: str):
        """撤销用户的所有token"""
        jids = []
        if email in cls._userTokens:
            for jid, _ in cls._userTokens[email]:
                jids.append(jid)
            del cls._userTokens[email]
        for jid in jids:
            cls._blacklist.add(jid)

    @classmethod
    async def isRevoked(cls, jid: str) -> bool:
        """检查token是否已被撤销"""
        return jid in cls._blacklist

    @classmethod
    async def cleanupExpiredTokens(cls):
        """清理过期的token记录"""
        now = int(time.time())
        for email in list(cls._userTokens.keys()):
            token_list = cls._userTokens[email]
            new_list = [(tid, exp) for tid, exp in token_list if exp > now]
            if new_list:
                cls._userTokens[email] = new_list
            else:
                del cls._userTokens[email]


async def generateToken(uid: int, email: str, expireDays: int = 7) -> str:
    """签发令牌"""
    kid, secret = await KeyManager.getKeyForSigning()
    now = int(time.time())
    expiredTimestamp = now + expireDays * 24 * 3600
    jid = secrets.token_urlsafe(16)
    payload = Payload(
        jid=jid,
        uid=uid,
        email=email,
        expired=expiredTimestamp,
        create=now
    )
    payloadDict = asdict(payload)
    await TokenManager.addToken(email, jid, expiredTimestamp)
    return pyjwt.encode(payloadDict, secret, algorithm="HS256", headers={"kid": kid})

async def verifyJwtPayload(token: str | None) -> Optional[Payload]:
    """验证并解析令牌"""
    try:
        if token is None:
            return None
        header = pyjwt.get_unverified_header(token)
        kid = header.get("kid")
        
        if not isinstance(kid, str):
            return None
        secret = await KeyManager.getKeyForVerifying(kid)
        if not secret:
            return None

        data = pyjwt.decode(token, secret, algorithms=["HS256"], audience=JWT_AUD, issuer=JWT_ISS)
        jid = data.get("jid")
        if jid is None:
            return None
        if await TokenManager.isRevoked(jid):
            logger.warning("Token is revoked")
            return None
        
        allowed_keys = Payload.__annotations__.keys()
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        
        return Payload(**filtered_data)
    except Exception:
        logger.error("JWT 验证失败", exc_info=True)

async def generateLoginToken(uid: int, email: str) -> str:
    """生成登录令牌"""
    return await generateToken(uid, email)

async def revokeUserTokens(email: str):
    """撤销用户的所有token"""
    await TokenManager.revokeTokensByUser(email)

async def revokeSingleToken(jid: str):
    """撤销单个token"""
    await TokenManager.revokeTokenById(jid)

async def cleanupExpiredTokens():
    """定期清理过期的token记录"""
    await TokenManager.cleanupExpiredTokens()
