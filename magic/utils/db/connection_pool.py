# -*- coding: utf-8 -*-
# lmoadll_bl platform
#
# @copyright  Copyright (c) 2025 lmoadll_bl team
# @license  GNU General Public License 3.0
"""
数据库连接池模块

提供线程安全的数据库连接池管理,支持连接复用、连接验证和空闲连接回收。
"""
import threading
import time
import logging
from collections.abc import Callable
from queue import Queue, Empty
from magic.utils.db.adapters.adapters import DatabaseAdapter, DatabaseFactory


try:
    import sqlite3
except ImportError:
    sqlite3 = None
try:
    import pymysql
except ImportError:
    pymysql = None
try:
    import psycopg2
except ImportError:
    psycopg2 = None


# 定义数据库异常元组
_db_exceptions: list[type[Exception]] = []
if sqlite3:
    _db_exceptions.append(sqlite3.Error)
if pymysql:
    _db_exceptions.append(pymysql.Error)
if psycopg2:
    _db_exceptions.append(psycopg2.Error)
_db_exceptions.append(Exception)
DB_EXCEPTIONS: tuple[type[Exception], ...] = tuple(_db_exceptions)


class ConnectionPool:
    """数据库连接池基类"""

    def __init__(self, db_type: str, config: dict[str, str], pool_size: int = 5, max_idle_time: int = 300):
        """
        初始化连接池

        :param db_type: 数据库类型
        :param config: 数据库配置
        :param pool_size: 连接池大小
        :param max_idle_time: 连接最大空闲时间(秒)
        """
        self.db_type: str = db_type
        self.config: dict[str, str] = config
        self.pool_size: int = pool_size
        self.max_idle_time: int = max_idle_time
        self.pool: Queue[DatabaseAdapter] = Queue(maxsize=pool_size)
        self.connection_count: int = 0
        self.lock: threading.RLock = threading.RLock()
        self.closed: bool = False

        # 预创建连接
        for _ in range(pool_size):
            _ = self._create_connection()

    def _create_connection(self) -> DatabaseAdapter | None:
        """创建新的数据库连接"""
        if self.closed:
            return None

        try:
            adapter = DatabaseFactory.create_adapter(self.db_type, self.config)
            adapter.connect()
            adapter.created_at = time.time()

            with self.lock:
                self.connection_count += 1

            return adapter
        except Exception as e:
            logging.error(f"创建数据库连接失败: {e}")
            return None

    def _is_connection_valid(self, adapter: DatabaseAdapter) -> bool:
        """验证连接是否有效"""
        idle_time: float = time.time() - adapter.created_at
        if idle_time > self.max_idle_time:
            return False

        # 尝试简单查询验证连接
        try:
            if adapter.db_type == "sqlite":
                adapter.execute("SELECT 1")
            else:
                adapter.execute("SELECT 1;")
            return True
        except DB_EXCEPTIONS:
            return False

    def _clean_transaction_state(self, adapter: DatabaseAdapter) -> None:
        """清理事务状态, 确保连接在不同线程间传递时的一致性"""
        try:
            adapter.rollback()
            # 安全地设置autocommit，处理不同数据库的实现差异
            connection = adapter.connection
            if connection is not None:
                # 使用getattr获取autocommit属性
                autocommit_attr: Callable[[bool], object] | object | None = getattr(
                    connection, "autocommit", None
                )
                if autocommit_attr is not None:
                    # 检查是否可调用
                    is_callable = callable(autocommit_attr)
                    if is_callable:
                        # 对于PyMySQL等，autocommit是一个方法
                        _ = autocommit_attr(True)
                    else:
                        # 对于SQLite、psycopg2等，autocommit是一个属性
                        # 使用setattr避免类型检查错误
                        setattr(connection, "autocommit", True)
        except DB_EXCEPTIONS:
            pass

    def get_connection(self) -> DatabaseAdapter:
        """从连接池获取连接"""
        if self.closed:
            raise RuntimeError("连接池已关闭")

        # 尝试从队列获取连接
        try:
            adapter = self.pool.get_nowait()
        except Empty:
            # 队列为空, 创建新连接
            adapter = self._create_connection()

        # 验证连接是否有效且未超时
        if adapter and self._is_connection_valid(adapter):
            # 清理事务状态
            self._clean_transaction_state(adapter)
            return adapter

        # 连接无效, 重新创建
        if adapter:
            try:
                adapter.disconnect()
                with self.lock:
                    self.connection_count -= 1
            except DB_EXCEPTIONS:
                pass

        # 重新创建连接
        adapter = self._create_connection()
        if adapter is None:
            raise RuntimeError("无法创建数据库连接")
        return adapter

    def return_connection(self, adapter: DatabaseAdapter) -> None:
        """归还连接到连接池"""
        if self.closed:
            return

        try:
            # 更新连接的最后使用时间
            adapter.created_at = time.time()
            # 尝试将连接放回队列
            self.pool.put_nowait(adapter)
        except Exception:
            # 如果队列已满或发生其他错误,关闭连接
            try:
                adapter.disconnect()
                with self.lock:
                    self.connection_count -= 1
            except DB_EXCEPTIONS:
                pass

    def close(self):
        """关闭连接池"""
        with self.lock:
            if self.closed:
                return
            self.closed = True

        # 关闭所有连接
        while True:
            try:
                adapter = self.pool.get_nowait()
                try:
                    adapter.disconnect()
                except DB_EXCEPTIONS:
                    pass
            except Empty:
                break

        with self.lock:
            self.connection_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type: None, exc_val: None, exc_tb: None) -> None:
        self.close()
