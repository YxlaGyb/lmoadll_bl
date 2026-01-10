#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORM核心模块

提供数据库连接池管理和ORM主类。
"""
# from typing import Any
from magic.utils.db.adapters.adapters import DatabaseAdapter
from magic.utils.db.connection_pool import ConnectionPool


class ORM:
    """
    ORM主类,管理多个数据库连接池
    
    提供数据库注册、连接获取和归还功能。
    """
    
    def __init__(self):
        """初始化ORM实例"""
        self._pools: dict[str, ConnectionPool] = {}
        self._default_db: str | None = None

    def register_db(self, name: str, db_type: str, config: dict[str, str], pool_size: int = 5) -> None:
        """
        注册数据库连接
        
        Args:
            name: 数据库名称
            db_type: 数据库类型 (sqlite/mysql/postgresql)
            config: 数据库配置字典
            pool_size: 连接池大小,默认为5
        
        Raises:
            ValueError: 当数据库类型不支持时
        """
        config["type"] = db_type  # 保存数据库类型
        
        # 创建连接池
        pool = ConnectionPool(db_type, config, pool_size=pool_size)
        self._pools[name] = pool
        
        # 如果是第一个注册的数据库,设置为默认数据库
        if self._default_db is None:
            self._default_db = name
    
    def get_db(self, name: str | None = None) -> DatabaseAdapter:
        """
        从连接池获取数据库连接
        
        Args:
            name: 数据库名称,如果为None则使用默认数据库
        
        Returns:
            数据库适配器实例
        
        Raises:
            ValueError: 当指定的数据库未注册时
        """
        if name is None:
            name = self._default_db
        
        if name not in self._pools:
            raise ValueError(f"未注册的数据库: {name}")
        
        # 从连接池获取连接
        return self._pools[name].get_connection()
    
    def return_db(self, adapter: DatabaseAdapter, name: str | None = None) -> None:
        """
        归还数据库连接到连接池
        
        Args:
            adapter: 数据库适配器实例
            name: 数据库名称,如果为None则使用默认数据库
        """
        if name is None:
            name = self._default_db
        
        if name in self._pools:
            self._pools[name].return_connection(adapter)
    
    def set_default_db(self, name: str) -> None:
        """
        设置默认数据库
        
        Args:
            name: 数据库名称
        
        Raises:
            ValueError: 当指定的数据库未注册时
        """
        if name not in self._pools:
            raise ValueError(f"未注册的数据库: {name}")
        
        self._default_db = name
    
    def close_all(self) -> None:
        """关闭所有连接池"""
        for pool in self._pools.values():
            pool.close()
        self._pools.clear()


db_orm = ORM()
