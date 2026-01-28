# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
密码哈希和验证模块

该模块提供密码哈希和验证功能, 基于Argon2密码哈希算法,
用于在应用程序中安全地存储和验证用户密码.
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import logging



__all__ = [
    'hashPassword', 
    'verifyPassword'
]

ph = PasswordHasher(
    time_cost=2,         # 迭代次数，推荐2-4
    memory_cost=102400,  # 内存开销（单位KB，如100MB）
    parallelism=2,       # 并行线程数
    hash_len=32,         # 输出哈希长度（字节）
    salt_len=16          # 盐值长度（字节）
)


def hashPassword(password: str):
    """对密码进行哈希处理"""
    try:
        if not password:
            print("密码必须是非空字符串")
            return None
        
        pw_hash = ph.hash(password)
        return pw_hash
    except Exception as e:
        logging.error(f"哈希处理失败: {e}")
        return None


def verifyPassword(pw_hash: str, password: str):
    """验证密码是否匹配哈希值"""
    try:
        if not pw_hash or not password:
            print("哈希值和密码必须是非空的")
            return False
            
        return ph.verify(pw_hash, password)
    except VerifyMismatchError:
        return False
    except Exception as e:
        logging.error(f"验证过程中出现错误喵: {e}")
        return False
