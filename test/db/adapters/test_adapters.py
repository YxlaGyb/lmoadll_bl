# -*- coding: utf-8 -*-
# lmoadll_bl platform
#
# @copyright  Copyright (c) 2025 lmoadll_bl team
# @license  GNU General Public License 3.0
"""
数据库适配器测试模块
测试 magic/utils/db/adapters/adapters.py 中的类和方法
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from magic.utils.db.adapters.adapters import (
    DatabaseAdapter,
    SQLiteAdapter,
    MySQLAdapter,
    PostgreSQLAdapter,
    DatabaseFactory,
)


class TestDatabaseAdapter:
    """测试 DatabaseAdapter 基类"""
    
    def test_database_adapter_initialization(self):
        """测试 DatabaseAdapter 初始化"""
        config = {
            "host": "localhost",
            "database": "test_db",
            "prefix": "test_"
        }
        
        adapter = DatabaseAdapter(config)
        
        assert adapter.config == config
        assert adapter.connection is None
        assert adapter.cursor is None
        assert adapter._in_transaction is False
        assert adapter.created_at == 0.0
        assert adapter.db_prefix == "test_"
        assert adapter.db_type is None
    
    def test_database_adapter_connect_not_implemented(self):
        """测试 connect 方法未实现"""
        adapter = DatabaseAdapter({})
        
        with pytest.raises(NotImplementedError):
            adapter.connect()
    
    def test_database_adapter_disconnect_without_connection(self):
        """测试断开没有连接的适配器"""
        adapter = DatabaseAdapter({})
        
        # 应该不会抛出异常
        adapter.disconnect()
        
        assert adapter.connection is None
        assert adapter.cursor is None
    
    def test_database_adapter_execute_without_cursor(self):
        """测试在没有游标的情况下执行查询"""
        adapter = DatabaseAdapter({})
        
        # 模拟 connect 方法
        mock_cursor = Mock()
        mock_cursor.execute = Mock()
        
        with patch.object(adapter, 'connect') as mock_connect:
            # 设置 connect 方法创建游标
            mock_connect.return_value = None
            # 在 connect 被调用后设置 cursor
            adapter.cursor = None  # 确保 cursor 为 None，这样 execute 会调用 connect
            
            # 当 connect 被调用时，设置 cursor
            def set_cursor():
                adapter.cursor = mock_cursor
            mock_connect.side_effect = set_cursor
            
            adapter.execute("SELECT 1")
            
            # 验证 connect 被调用
            mock_connect.assert_called_once()
            # 验证 execute 被调用
            mock_cursor.execute.assert_called_once_with("SELECT 1")
    
    def test_database_adapter_execute_with_params(self):
        """测试带参数的查询执行"""
        adapter = DatabaseAdapter({})
        adapter.cursor = Mock()
        adapter.cursor.execute = Mock()
        
        adapter.execute("SELECT * FROM users WHERE id = %s", (1,))
        
        adapter.cursor.execute.assert_called_once_with("SELECT * FROM users WHERE id = %s", (1,))
    
    def test_database_adapter_fetchone_without_cursor(self):
        """测试在没有游标的情况下获取单条记录"""
        adapter = DatabaseAdapter({})
        
        with pytest.raises(RuntimeError, match="没有活动的游标"):
            adapter.fetchone()
    
    def test_database_adapter_fetchall_without_cursor(self):
        """测试在没有游标的情况下获取所有记录"""
        adapter = DatabaseAdapter({})
        
        with pytest.raises(RuntimeError, match="没有活动的游标"):
            adapter.fetchall()
    
    def test_database_adapter_commit_without_connection(self):
        """测试在没有连接的情况下提交事务"""
        adapter = DatabaseAdapter({})
        
        # 应该不会抛出异常
        adapter.commit()
        
        assert adapter._in_transaction is False
    
    def test_database_adapter_rollback_without_connection(self):
        """测试在没有连接的情况下回滚事务"""
        adapter = DatabaseAdapter({})
        
        # 应该不会抛出异常
        adapter.rollback()
        
        assert adapter._in_transaction is False
    
    def test_database_adapter_begin_transaction(self):
        """测试开始事务"""
        adapter = DatabaseAdapter({})
        
        adapter.begin_transaction()
        
        assert adapter._in_transaction is True
        
        # 再次开始事务应该不会改变状态
        adapter.begin_transaction()
        assert adapter._in_transaction is True
    
    def test_database_adapter_close(self):
        """测试关闭连接"""
        adapter = DatabaseAdapter({})
        
        # 模拟 disconnect 方法
        with patch.object(adapter, 'disconnect') as mock_disconnect:
            adapter.close()
            mock_disconnect.assert_called_once()


class TestDatabaseFactory:
    """测试 DatabaseFactory 工厂类"""
    
    def test_create_sqlite_adapter(self):
        """测试创建 SQLite 适配器"""
        config = {"path": "/tmp/test.db"}
        
        adapter = DatabaseFactory.create_adapter("sqlite", config)
        
        assert isinstance(adapter, SQLiteAdapter)
        assert adapter.config == config
    
    def test_create_mysql_adapter(self):
        """测试创建 MySQL 适配器"""
        config = {
            "host": "localhost",
            "database": "test_db"
        }
        
        adapter = DatabaseFactory.create_adapter("mysql", config)
        
        assert isinstance(adapter, MySQLAdapter)
        assert adapter.config == config
    
    def test_create_postgresql_adapter(self):
        """测试创建 PostgreSQL 适配器"""
        config = {
            "host": "localhost",
            "database": "test_db"
        }
        
        adapter = DatabaseFactory.create_adapter("postgresql", config)
        
        assert isinstance(adapter, PostgreSQLAdapter)
        assert adapter.config == config
    
    def test_create_adapter_invalid_type(self):
        """测试创建无效类型的适配器"""
        config = {}
        
        with pytest.raises(ValueError, match="不支持的数据库类型: invalid_db"):
            DatabaseFactory.create_adapter("invalid_db", config)


class TestSQLiteAdapter:
    """测试 SQLiteAdapter 类"""
    
    def test_sqlite_adapter_initialization(self):
        """测试 SQLiteAdapter 初始化"""
        config = {"path": "/tmp/test.db", "prefix": "test_"}
        
        adapter = SQLiteAdapter(config)
        
        assert adapter.config == config
        assert adapter.db_prefix == "test_"
        assert adapter.db_type is None
    
    @patch('magic.utils.db.adapters.adapters.sqlite3')
    def test_sqlite_adapter_connect_success(self, mock_sqlite3):
        """测试 SQLite 连接成功"""
        config = {"path": "/tmp/test.db"}
        
        # 模拟 sqlite3 模块
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_sqlite3.connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        adapter = SQLiteAdapter(config)
        
        # 模拟 _initialize_tables 方法
        with patch.object(adapter, '_initialize_tables') as mock_init_tables:
            adapter.connect()
            
            # 验证连接被创建
            mock_sqlite3.connect.assert_called_once_with("/tmp/test.db", check_same_thread=False)
            # 验证游标被创建
            mock_connection.cursor.assert_called_once()
            # 验证表初始化被调用
            mock_init_tables.assert_called_once()
            
            assert adapter.connection == mock_connection
            assert adapter.cursor == mock_cursor
    
    @patch('magic.utils.db.adapters.adapters.sqlite3', None)
    def test_sqlite_adapter_connect_sqlite3_not_installed(self):
        """测试 SQLite3 模块未安装的情况"""
        config = {"path": "/tmp/test.db"}
        adapter = SQLiteAdapter(config)
        
        with pytest.raises(ImportError, match="sqlite3模块未安装"):
            adapter.connect()
    
    def test_sqlite_adapter_connect_no_path(self):
        """测试 SQLite 连接没有路径配置"""
        config = {}
        adapter = SQLiteAdapter(config)
        
        with pytest.raises(ValueError, match="SQLite数据库路径未配置"):
            adapter.connect()
    
    def test_sqlite_adapter_get_create_users_sql(self):
        """测试获取创建 users 表的 SQL 语句"""
        config = {"prefix": "test_"}
        adapter = SQLiteAdapter(config)
        
        sql = adapter._get_create_users_sql("test_users")
        
        assert "CREATE TABLE IF NOT EXISTS test_users" in sql
        assert "uid INTEGER NOT NULL PRIMARY KEY" in sql
        assert '"group" VARCHAR(16) DEFAULT' in sql
    
    def test_sqlite_adapter_get_create_options_sql(self):
        """测试获取创建 options 表的 SQL 语句"""
        config = {"prefix": "test_"}
        adapter = SQLiteAdapter(config)
        
        sql = adapter._get_create_options_sql("test_options")
        
        assert "CREATE TABLE IF NOT EXISTS test_options" in sql
        assert "name VARCHAR(32) NOT NULL" in sql
        assert "user INT(10) DEFAULT '0' NOT NULL" in sql
    
    def test_sqlite_adapter_get_create_usermeta_sql(self):
        """测试获取创建 usermeta 表的 SQL 语句"""
        config = {"prefix": "test_"}
        adapter = SQLiteAdapter(config)
        
        sql = adapter._get_create_usermeta_sql("test_usermeta", "test_users")
        
        assert "CREATE TABLE IF NOT EXISTS test_usermeta" in sql
        assert "umeta_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT" in sql
        assert "FOREIGN KEY (user_id) REFERENCES test_users" in sql


class TestMySQLAdapter:
    """测试 MySQLAdapter 类"""
    
    def test_mysql_adapter_initialization(self):
        """测试 MySQLAdapter 初始化"""
        config = {
            "host": "localhost",
            "database": "test_db",
            "prefix": "test_"
        }
        
        adapter = MySQLAdapter(config)
        
        assert adapter.config == config
        assert adapter.db_prefix == "test_"
        assert adapter.db_type is None
    
    @patch('magic.utils.db.adapters.adapters.pymysql')
    def test_mysql_adapter_connect_success(self, mock_pymysql):
        """测试 MySQL 连接成功"""
        config = {
            "host": "localhost",
            "port": "3306",
            "user": "test_user",
            "password": "test_pass",
            "database": "test_db"
        }
        
        # 模拟 pymysql 模块
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_pymysql.connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        adapter = MySQLAdapter(config)
        
        # 模拟 _initialize_tables 方法
        with patch.object(adapter, '_initialize_tables') as mock_init_tables:
            adapter.connect()
            
            # 验证连接被创建
            mock_pymysql.connect.assert_called_once_with(
                host="localhost",
                port=3306,
                user="test_user",
                password="test_pass",
                database="test_db",
                charset="utf8mb4",
                cursorclass=mock_pymysql.cursors.DictCursor
            )
            # 验证游标被创建
            mock_connection.cursor.assert_called_once()
            # 验证表初始化被调用
            mock_init_tables.assert_called_once()
            
            assert adapter.connection == mock_connection
            assert adapter.cursor == mock_cursor
    
    @patch('magic.utils.db.adapters.adapters.pymysql', None)
    def test_mysql_adapter_connect_pymysql_not_installed(self):
        """测试 PyMySQL 模块未安装的情况"""
        config = {"host": "localhost"}
        adapter = MySQLAdapter(config)
        
        with pytest.raises(ImportError, match="pymysql模块未安装"):
            adapter.connect()
    
    def test_mysql_adapter_get_create_users_sql(self):
        """测试获取创建 users 表的 SQL 语句"""
        config = {"prefix": "test_"}
        adapter = MySQLAdapter(config)
        
        sql = adapter._get_create_users_sql("test_users")
        
        assert "CREATE TABLE IF NOT EXISTS test_users" in sql
        assert "uid INT NOT NULL PRIMARY KEY AUTO_INCREMENT" in sql
        assert "`group` VARCHAR(16) DEFAULT 'visitor'" in sql
        assert "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4" in sql
    
    def test_mysql_adapter_get_create_options_sql(self):
        """测试获取创建 options 表的 SQL 语句"""
        config = {"prefix": "test_"}
        adapter = MySQLAdapter(config)
        
        sql = adapter._get_create_options_sql("test_options")
        
        assert "CREATE TABLE IF NOT EXISTS test_options" in sql
        assert "name VARCHAR(32) NOT NULL" in sql
        assert "user INT(10) DEFAULT '0' NOT NULL" in sql
        assert "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4" in sql
    
    def test_mysql_adapter_get_create_usermeta_sql(self):
        """测试获取创建 usermeta 表的 SQL 语句"""
        config = {"prefix": "test_"}
        adapter = MySQLAdapter(config)
        
        sql = adapter._get_create_usermeta_sql("test_usermeta", "test_users")
        
        assert "CREATE TABLE IF NOT EXISTS test_usermeta" in sql
        assert "umeta_id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT" in sql
        assert "FOREIGN KEY (user_id) REFERENCES test_users" in sql
        assert "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4" in sql


class TestPostgreSQLAdapter:
    """测试 PostgreSQLAdapter 类"""
    
    def test_postgresql_adapter_initialization(self):
        """测试 PostgreSQLAdapter 初始化"""
        config = {
            "host": "localhost",
            "database": "test_db",
            "prefix": "test_"
        }
        
        adapter = PostgreSQLAdapter(config)
        
        assert adapter.config == config
        assert adapter.db_prefix == "test_"
        assert adapter.db_type is None
    
    @patch('magic.utils.db.adapters.adapters.psycopg2')
    def test_postgresql_adapter_connect_success(self, mock_psycopg2):
        """测试 PostgreSQL 连接成功"""
        config = {
            "host": "localhost",
            "port": "5432",
            "user": "test_user",
            "password": "test_pass",
            "database": "test_db"
        }
        
        # 模拟 psycopg2 模块
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_psycopg2.connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        adapter = PostgreSQLAdapter(config)
        
        # 模拟 _initialize_tables 方法
        with patch.object(adapter, '_initialize_tables') as mock_init_tables:
            adapter.connect()
            
            # 验证连接被创建
            mock_psycopg2.connect.assert_called_once_with(
                host="localhost",
                port=5432,
                user="test_user",
                password="test_pass",
                database="test_db"
            )
            # 验证游标被创建
            mock_connection.cursor.assert_called_once()
            # 验证表初始化被调用
            mock_init_tables.assert_called_once()
            
            assert adapter.connection == mock_connection
            assert adapter.cursor == mock_cursor
    
    @patch('magic.utils.db.adapters.adapters.psycopg2', None)
    def test_postgresql_adapter_connect_psycopg2_not_installed(self):
        """测试 psycopg2 模块未安装的情况"""
        config = {"host": "localhost"}
        adapter = PostgreSQLAdapter(config)
        
        with pytest.raises(ImportError, match="psycopg2模块未安装"):
            adapter.connect()
    
    def test_postgresql_adapter_get_create_users_sql(self):
        """测试获取创建 users 表的 SQL 语句"""
        config = {"prefix": "test_"}
        adapter = PostgreSQLAdapter(config)
        
        sql = adapter._get_create_users_sql("test_users")
        
        assert "CREATE TABLE IF NOT EXISTS test_users" in sql
        assert "uid SERIAL NOT NULL PRIMARY KEY" in sql
        assert '"group" VARCHAR(16) DEFAULT' in sql
    
    def test_postgresql_adapter_get_create_options_sql(self):
        """测试获取创建 options 表的 SQL 语句"""
        config = {"prefix": "test_"}
        adapter = PostgreSQLAdapter(config)
        
        sql = adapter._get_create_options_sql("test_options")
        
        assert "CREATE TABLE IF NOT EXISTS test_options" in sql
        assert "name VARCHAR(32) NOT NULL" in sql
        assert "user INTEGER DEFAULT 0 NOT NULL" in sql
    
    def test_postgresql_adapter_get_create_usermeta_sql(self):
        """测试获取创建 usermeta 表的 SQL 语句"""
        config = {"prefix": "test_"}
        adapter = PostgreSQLAdapter(config)
        
        sql = adapter._get_create_usermeta_sql("test_usermeta", "test_users")
        
        assert "CREATE TABLE IF NOT EXISTS test_usermeta" in sql
        assert "umeta_id SERIAL NOT NULL PRIMARY KEY" in sql
        assert "FOREIGN KEY (user_id) REFERENCES test_users" in sql
    
    def test_postgresql_adapter_execute_with_params(self):
        """测试 PostgreSQL 适配器的 execute 方法"""
        config = {}
        adapter = PostgreSQLAdapter(config)
        
        # 模拟 cursor
        mock_cursor = Mock()
        mock_cursor.execute = Mock()
        adapter.cursor = mock_cursor
        
        adapter.execute("SELECT * FROM users WHERE id = %s", (1,))
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users WHERE id = %s", (1,))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
