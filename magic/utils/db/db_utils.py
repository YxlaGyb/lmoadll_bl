#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库工具函数模块

提供与数据库操作相关的辅助函数。
"""
import logging
import time
from magic.utils.TomlConfig import DoesitexistConfigToml, WriteConfigToml
from magic.utils.db.orm import db_orm


def GetDbConnection(tablename=None):
    """从连接池获取数据库连接"""
    try:
        db_type = DoesitexistConfigToml("db", "sql_rd")
        db_prefix = DoesitexistConfigToml("db", "sql_prefix")

        if not db_type or not db_prefix:
            return [False, "数据库配置缺失", None, None, None]

        # 确保default数据库已注册到连接池
        if "default" not in db_orm._pools:
            if db_type == "sqlite":
                sql_sqlite_path = DoesitexistConfigToml("db", "sql_sqlite_path")
                if not sql_sqlite_path:
                    return [False, "SQLite路径配置缺失", None, None, None]
                db_orm.register_db(
                    "default",
                    "sqlite",
                    {"path": sql_sqlite_path, "prefix": db_prefix, "type": "sqlite"},
                )

            elif db_type == "mysql":
                # 从配置中获取MySQL连接信息
                db_host = DoesitexistConfigToml("db", "sql_host")
                db_port = DoesitexistConfigToml("db", "sql_port")
                db_name = DoesitexistConfigToml("db", "sql_database")
                db_user = DoesitexistConfigToml("db", "sql_user")
                db_password = DoesitexistConfigToml("db", "sql_password")
                db_orm.register_db(
                    "default",
                    "mysql",
                    {
                        "host": db_host,
                        "port": db_port,
                        "user": db_user,
                        "password": db_password,
                        "database": db_name,
                        "prefix": db_prefix,
                        "type": "mysql",
                    },
                )

            elif db_type == "postgresql":
                # 从配置中获取PostgreSQL连接信息
                db_host = DoesitexistConfigToml("db", "sql_host")
                db_port = DoesitexistConfigToml("db", "sql_port")
                db_name = DoesitexistConfigToml("db", "sql_database")
                db_user = DoesitexistConfigToml("db", "sql_user")
                db_password = DoesitexistConfigToml("db", "sql_password")
                db_orm.register_db(
                    "default",
                    "postgresql",
                    {
                        "host": db_host,
                        "port": db_port,
                        "user": db_user,
                        "password": db_password,
                        "database": db_name,
                        "prefix": db_prefix,
                        "type": "postgresql",
                    },
                )
            else:
                return [False, f"不支持的数据库类型: {db_type}", None, None, None]

        db = db_orm.get_db("default")
        table_name = f"{db_prefix}{tablename}" if tablename else None
        return [True, "数据库连接成功", db, db.cursor, table_name]
    except Exception as e:
        return [False, str(e), None, None, None]


def CheckSuperadminExists(admin_username, admin_email, admin_password, db_prefix=None, db_config=None):
    """检查超级管理员是否存在
    
    Args:
        admin_username: 管理员用户名
        admin_email: 管理员邮箱
        admin_password: 管理员密码
        db_prefix: 数据库表前缀（可选，默认为配置中的前缀）
        db_config: 数据库配置字典（可选，用于安装过程中的临时配置）
    """
    db = None
    try:
        # 如果提供了数据库配置，优先使用它（安装过程）
        if db_config:
            if "default" not in db_orm._pools:
                db_type = db_config.get("type", "sqlite")
                db_orm.register_db("default", db_type, db_config)
        else:
            # 使用统一的数据库连接获取方式（正常运行过程）
            success, message, db, cursor, table_name = GetDbConnection("users")
            if not success:
                return [False, message]
            
            # 从配置中获取数据库前缀
            db_prefix = DoesitexistConfigToml("db", "sql_prefix")
            if not db_prefix:
                return [False, "数据库前缀配置缺失"]

        db = db_orm.get_db("default")
        table_name = f"{db_prefix}users"
        db.execute(
            f"SELECT COUNT(*) FROM {table_name} WHERE `group` = ?",
            ("superadministrator",),
        )
        count = db.fetchone()[0]

        if count > 0:
            return [False, "超级管理员账号已存在"]

        current_time = int(time.time())
        db.execute(
            f"INSERT INTO {table_name} (name, password, mail, createdAt, isActive, `group`) VALUES (?, ?, ?, ?, ?, ?)",
            (
                admin_username,
                admin_password,
                admin_email,
                current_time,
                1,
                "superadministrator",
            ),
        )
        db.commit()

        return [True, "超级管理员账号创建成功"]
    except Exception as e:
        return [False, str(e)]
    finally:
        if db:
            db_orm.return_db(db, "default")


def CreateSiteOption(db_prefix: str, sql_sqlite_path: str, option_name: str, option_value: str, user_id: int = 0) -> list[Union[bool, str]]:
    """创建网站选项"""
    db = None
    try:
        success, message, db, cursor, table_name = GetDbConnection("options")
        if not success:
            return [False, message]
        table_name = f"{db_prefix}options"
        db = db_orm.get_db("default")

        db.execute(
            f"INSERT INTO {table_name} (name, user, value) VALUES (?, ?, ?)",
            (option_name, user_id, option_value),
        )
        db.commit()

        return [True, "网站选项创建成功"]
    except Exception as e:
        logging.error(f"创建网站选项失败: {e}")
        return [False, str(e)]
    finally:
        if db:
            db_orm.return_db(db, "default")


def InitVerificationDbConn(db_type: str, **kwargs) -> list[union[bool, Union[int, str]]]:
    """初始化数据库连接验证"""
    try:
        if db_type == "sqlite":
            db_path = kwargs.get("sql_sqlite_path", "")
            db_prefix = kwargs.get("db_prefix", "")

            # 保存配置
            WriteConfigToml("db", "sql_rd", "sqlite")
            WriteConfigToml("db", "sql_prefix", db_prefix)
            WriteConfigToml("db", "sql_sqlite_path", db_path)

            db_orm.register_db(
                "default",
                "sqlite",
                {"path": db_path, "prefix": db_prefix, "type": "sqlite"},
            )
            # 测试连接
            db = db_orm.get_db()
            db.connect()
            db.disconnect()
            return [True, 0]
        
        elif db_type == "mysql":
            db_prefix = kwargs.get("db_prefix", "")
            db_host = kwargs.get("sql_host", "localhost")
            db_port = kwargs.get("sql_port", 3306)
            db_name = kwargs.get("sql_database", "lmoadll_bl")
            db_user = kwargs.get("sql_user", "root")
            db_password = kwargs.get("sql_password", "")
            db_orm.register_db(
                "default",
                "mysql",
                {
                    "host": db_host,
                    "port": db_port,
                    "user": db_user,
                    "password": db_password,
                    "database": db_name,
                    "prefix": db_prefix,
                },
            )
            # 测试连接
            db = db_orm.get_db()
            db.connect()
            db.disconnect()
            return [True, 0]
        
        elif db_type == "postgresql":
            db_prefix = kwargs.get("db_prefix", "")
            db_host = kwargs.get("sql_host", "localhost")
            db_port = kwargs.get("sql_port", 5432)
            db_name = kwargs.get("sql_database", "lmoadll_bl")
            db_user = kwargs.get("sql_user", "postgres")
            db_password = kwargs.get("sql_password", "")
            db_orm.register_db(
                "default",
                "postgresql",
                {
                    "host": db_host,
                    "port": db_port,
                    "user": db_user,
                    "password": db_password,
                    "database": db_name,
                    "prefix": db_prefix,
                },
            )
            # 测试连接
            db = db_orm.get_db()
            db.connect()
            db.disconnect()

            return [True, 0]
        else:
            return [False, f"不支持的数据库类型: {db_type}"]
    except Exception as e:
        return [False, str(e)]


def GetOrSetSiteOption(db_prefix: str,sql_sqlite_path: str,option_name: str,option_value: Optional[str] = None,user_id: int = 0) -> List[Union[bool, str]]:
    """获取或设置网站选项"""
    db = None
    try:
        success, message, db, cursor, table_name = GetDbConnection("options")
        if not success:
            return [False, message]
        table_name = f"{db_prefix}options"
        db = db_orm.get_db("default")

        # 如果提供了option_value,则设置或更新选项
        if option_value is not None:
            # 检查选项是否已存在
            db.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE name = ? AND user = ?",
                (option_name, user_id),
            )
            count = db.fetchone()[0]

            if count > 0:
                db.execute(
                    f"UPDATE {table_name} SET value = ? WHERE name = ? AND user = ?",
                    (option_value, option_name, user_id),
                )
            else:
                db.execute(
                    f"INSERT INTO {table_name} (name, user, value) VALUES (?, ?, ?)",
                    (option_name, user_id, option_value),
                )

            db.commit()
            return [True, "网站选项设置成功"]
        else:
            db.execute(
                f"SELECT value FROM {table_name} WHERE name = ? AND user = ?",
                (option_name, user_id),
            )
            result = db.fetchone()

            if result:
                return [True, result[0]]
            return [False, "选项不存在"]
    except Exception as e:
        return [False, str(e)]
    finally:
        if db:
            db_orm.return_db(db, "default")


def GetSiteOptionByName(option_name: str):
    """查询网站设置"""
    success, message, db, cursor, _ = GetDbConnection("users")
    if not success:
        return [False, message]

    try:
        db_prefix = DoesitexistConfigToml("db", "sql_prefix")
        if not db_prefix:
            return [False, "数据库前缀配置缺失"]
        table_name = f"{db_prefix}options"
        db = db_orm.get_db("default")
        db.execute(
            f"SELECT name, user, value FROM {table_name} WHERE name = ?", (option_name,)
        )
        result = db.fetchone()

        if result:
            name, user, value = result
            """
            为了安全,先判断user是否为0
                - True, 返回name、user、value
                - False, 跳过, 等后面添加功能
            """
            if user == 0:
                return [True, {"name": name, "user": user, "value": value}]
            else:
                return [True, None]
        else:
            return [False, "未找到指定的设置"]
    except Exception as e:
        logging.error(f"查询网站设置失败: {e}")
        return [False, str(e)]
    finally:
        if db:
            db_orm.return_db(db, "default")


def GetUserByEmail(username_email: str):
    """根据用户名或邮箱获取用户信息"""
    db = None
    try:
        success, message, db, cursor, table_name = GetDbConnection("users")
        if not success:
            logging.error(f"数据库连接失败: {message}")
            return None
        db = db_orm.get_db("default")
        db.execute(
            f"SELECT uid, name, password, mail, `group` FROM {table_name} WHERE mail = ?",
            (username_email,),
        )
        user = db.fetchone()

        if user:
            return {
                "uid": user[0],
                "name": user[1],
                "password": user[2],
                "email": user[3],
                "group": user[4],
            }
        return None
    except Exception as e:
        logging.error(f"查询用户信息失败: {e}")
        return None
    finally:
        if db:
            db_orm.return_db(db, "default")


def GetUserRoleByIdentity(user_identity: int) -> Union[list[Union[bool, str]], Optional[tuple[str, ...]]]:
    """通过用户的uid查找用户的身份权限"""
    success, message, db, cursor, table_name = GetDbConnection("users")
    if not success:
        return [False, message]
    db = db_orm.get_db("default")

    try:
        db.execute(f"SELECT `group` FROM {table_name} WHERE uid = ?", (user_identity,))
        user_group = db.fetchone()

        # 统一处理不同驱动返回类型（dict, 序列/元组, sqlite3.Row, None）
        if not user_group:
            return None

        # dict 情况(如 pymysql DictCursor)
        if isinstance(user_group, dict):
            group_val = user_group.get("group") or user_group.get("group")
            return (str(group_val),) if group_val is not None else None

        # 序列或可索引对象(如 psycopg2/SQLite 返回的 tuple 或 Row)
        try:
            first = user_group[0]
            return (str(first),)
        except Exception:
            # 回退：尝试通过属性或映射访问
            if hasattr(user_group, "get"):
                group_val = user_group.get("group")
                return (str(group_val),) if group_val is not None else None
            return None
    except Exception as e:
        logging.error(f"查询用户角色失败: {e}")
        return [False, str(e)]
    finally:
        if db:
            db_orm.return_db(db, "default")


def GetUserNameByIdentity(user_identity: int):
    """通过用户的uid查找用户名"""
    success, message, db, cursor, table_name = GetDbConnection("users")
    if not success:
        return [False, message]
    db = db_orm.get_db("default")

    try:
        db.execute(f"SELECT name FROM {table_name} WHERE uid = ?", (user_identity,))
        user_name = db.fetchone()
        return user_name  # 期望返回,如: ('admin',)
    except Exception as e:
        logging.error(f"查询用户名失败: {e}")
        return [False, str(e)]
    finally:
        if db:
            db_orm.return_db(db, "default")


def GetUserCount():
    """获取用户数量"""
    success, message, db, cursor, table_name = GetDbConnection("users")
    if not success:
        return [False, message]
    db = db_orm.get_db("default")

    try:
        db.execute(f"SELECT COUNT(*) FROM {table_name}")
        user_count = db.fetchone()[0]
        return user_count
    except Exception as e:
        logging.error(f"查询用户数量失败: {e}")
        return [False, str(e)]
    finally:
        if db:
            db_orm.return_db(db, "default")


def SearchUsers(keyword: str) -> Union[list[Union[bool, str]], list[dict[str, Any]]]:
    """
    根据关键词搜索用户
    支持搜索用户ID、姓名或邮箱
    
    :param keyword: 搜索关键词
    :return: 用户列表或错误信息
    """
    success, message, db, cursor, table_name = GetDbConnection("users")
    if not success:
        return [False, message]
    db = db_orm.get_db("default")

    try:
        # 尝试将关键词转换为整数
        user_id = None
        try:
            user_id = int(keyword)
        except ValueError:
            pass
        
        if user_id is not None:
            # 根据用户ID精确搜索
            db.execute(f"SELECT uid, name, mail FROM {table_name} WHERE uid = ?", (user_id,))
        else:
            # 根据姓名或邮箱模糊搜索
            search_pattern = f"%{keyword}%"
            db.execute(f"SELECT uid, name, mail FROM {table_name} WHERE name LIKE ? OR mail LIKE ? LIMIT 50", 
                      (search_pattern, search_pattern))
        
        users = db.fetchall()
        # 转换为字典列表
        user_list = []
        for user in users:
            user_list.append({
                'id': user[0],
                'name': user[1],
                'email': user[2]
            })
        return user_list
    except Exception as e:
        logging.error(f"搜索用户失败: {e}")
        return [False, str(e)]
    finally:
        if db:
            db_orm.return_db(db, "default")

