# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0


import os
import random
import string
from quart import Response, request, send_file, jsonify, abort
from functools import wraps
from magic.utils.TomlConfig import DoesitexistConfigToml, WriteConfigToml
from magic.utils.Argon2Password import HashPassword
from magic.utils.db import (
    db_orm,
    UserModel,
    OptionModel,
    InitVerificationDbConn,
    CheckSuperadminExists,
    GetOrSetSiteOption,
)


def install_permissions(f):
    @wraps(f)
    def per_install(*args, **kwargs):
        if DoesitexistConfigToml("server", "install"):
            return f(*args, **kwargs)
        else:
            return abort(404)

    return per_install


class install:
    @staticmethod
    @install_permissions
    def install_index() -> Response:
        return send_file("admin/base/install.html")


    @staticmethod
    @install_permissions
    def check_database_configuration() -> Response: # type: ignore
        """判断是否有配置过数据库"""
        if (
            DoesitexistConfigToml("db", "sql_rd") == "sqlite"
            and DoesitexistConfigToml("db", "sql_prefix") != ""
            and os.path.exists(DoesitexistConfigToml("db", "sql_sqlite_path"))
        ):
            # [ ] TODO : 检查数据库是否存在
            pass


    @staticmethod
    @install_permissions
    def get_sqlite_path() -> Response:
        """获取数据库路径, 自动生成路径and return"""
        data = request.get_json()
        db_type = data.get("db_type")

        if db_type == "sqlite":
            content_dir = "contents"
            os.makedirs(content_dir, exist_ok=True)

            random_name = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=10)
            )
            db_filename = f"{random_name}.db"
            default_path = os.path.abspath(os.path.join(content_dir, db_filename))

            return jsonify({"path": default_path})

        return jsonify({"error": "无效的数据库类型"})


    @staticmethod
    @install_permissions
    def install_verification_db_conn() -> Response:
        """测试数据库连接并保持配置"""
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "message": "请求的数据为空"})

        db_type = data.get("db_type")
        if not db_type:
            return jsonify({"success": False, "message": "数据库类型不能为空"})

        db_config = {"db_prefix": data.get("db_prefix", "lmoadll_")}

        if db_type == "sqlite":
            sql_sqlite_path = data.get("sql_sqlite_path")
            if not sql_sqlite_path:
                return jsonify({"success": False, "message": "SQLite数据库路径不能为空"})
            db_config["sql_sqlite_path"] = sql_sqlite_path
        elif db_type == "mysql":
            db_config["db_host"] = data.get("db_host", "localhost")
            db_config["db_port"] = data.get("db_port", 3306)
            db_config["db_name"] = data.get("db_name", "")
            db_config["db_user"] = data.get("db_user", "")
            db_config["db_password"] = data.get("db_password", "")

            # 检查MySQL必要参数
            if not db_config["db_name"] or not db_config["db_user"]:
                return jsonify(
                    {"success": False, "message": "MySQL数据库名称和用户名不能为空"}
                )
        elif db_type == "postgresql":
            db_config["db_host"] = data.get("db_host", "localhost")
            db_config["db_port"] = data.get("db_port", 5432)
            db_config["db_name"] = data.get("db_name", "")
            db_config["db_user"] = data.get("db_user", "")
            db_config["db_password"] = data.get("db_password", "")

            # 检查PostgreSQL必要参数
            if not db_config["db_name"] or not db_config["db_user"]:
                return jsonify(
                    {"success": False, "message": "PostgreSQL数据库名称和用户名不能为空"}
                )
        else:
            return jsonify({"success": False, "message": f"不支持的数据库类型: {db_type}"})

        # 使用ORM的统一数据库连接验证函数
        result = InitVerificationDbConn(db_type, **db_config)
        if result[0]:
            return jsonify({"success": True, "message": f"{db_type}连接成功"})
        else:
            return jsonify({"success": False, "message": f"数据库连接错误喵: {result[1]}"})


    @staticmethod
    @install_permissions
    def create_admin_account() -> Response:
        """创建超级管理员账号并保存配置"""
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "message": "请求的数据为空"})

        # 获取表单数据
        site_name = data.get("site_name")
        site_url = data.get("site_url")
        superadministrator_email = data.get("superadministrator_email")
        superadministrator_username = data.get("superadministrator_username")
        superadministrator_password = data.get("superadministrator_password")

        # 验证必填字段
        if (
            not site_name
            or not site_url
            or not superadministrator_email
            or not superadministrator_username
            or not superadministrator_password
        ):
            return jsonify({"success": False, "message": "请填写所有必填字段"})

        try:
            hashed_password = HashPassword(superadministrator_password)
            if not hashed_password:
                return jsonify({"success": False, "message": "密码加密失败"})

            # 获取并保存数据库配置
            db_type = data.get("db_type")
            if not db_type:
                return jsonify({"success": False, "message": "数据库类型不能为空"})

            if db_type == "sqlite":
                # 获取SQLite配置
                db_prefix = data.get("db_prefix", "lmoadll_")
                sql_sqlite_path = data.get("sql_sqlite_path")

                if not sql_sqlite_path:
                    return jsonify(
                        {"success": False, "message": "SQLite数据库路径不能为空"}
                    )

                GetOrSetSiteOption(db_prefix, sql_sqlite_path, "site_name", site_name)
                GetOrSetSiteOption(db_prefix, sql_sqlite_path, "site_url", site_url)

                # 在数据库中创建超级管理员账号
                db_config = {
                    "type": "sqlite",
                    "path": sql_sqlite_path,
                    "prefix": db_prefix
                }
                result = CheckSuperadminExists(
                    superadministrator_username,
                    superadministrator_email,
                    hashed_password,
                    db_prefix=db_prefix,
                    db_config=db_config
                )
                if not result[0]:
                    return jsonify(
                        {"success": False, "message": f"创建管理员账号失败: {result[1]}"}
                    )
            elif db_type == "mysql":
                # 使用ORM系统的创建MySQL数据库的超级管理员
                db_host = data.get("db_host", "localhost")
                db_port = data.get("db_port", 3306)
                db_name = data.get("db_name", "")
                db_user = data.get("db_user", "")
                db_password = data.get("db_password", "")
                db_prefix = data.get("db_prefix", "lmoadll_")

                # 验证MySQL参数
                if not db_name or not db_user:
                    return jsonify(
                        {"success": False, "message": "MySQL数据库名称和用户名不能为空"}
                    )

                # 注册MySQL数据库
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

                # 获取数据库连接
                db = db_orm.get_db()
                db.connect()

                try:
                    # 设置表名
                    UserModel.set_table_name(f"{db_prefix}users")
                    OptionModel.set_table_name(f"{db_prefix}options")

                    # 保存网站配置
                    OptionModel.create(db, name="site_name", user=0, value=site_name)
                    OptionModel.create(db, name="site_url", user=0, value=site_url)

                    # 检查超级管理员是否已存在
                    superadmins = UserModel.find(db, group="superadministrator")
                    if superadmins and len(superadmins) > 0:
                        return jsonify(
                            {"success": False, "message": "超级管理员账号已存在"}
                        )

                    # 创建超级管理员账号
                    import time

                    current_time = int(time.time())

                    UserModel.create(
                        db,
                        name=superadministrator_username,
                        password=hashed_password,
                        mail=superadministrator_email,
                        createdAt=current_time,
                        isActive=1,
                        group="superadministrator",
                    )

                    db.commit()
                except Exception as e:
                    db.rollback()
                    return jsonify(
                        {"success": False, "message": f"创建管理员账号失败: {str(e)}"}
                    )
                finally:
                    db.disconnect()
            elif db_type == "postgresql":
                # 使用ORM系统创建PostgreSQL数据库的超级管理员
                db_host = data.get("db_host", "localhost")
                db_port = data.get("db_port", 5432)
                db_name = data.get("db_name", "")
                db_user = data.get("db_user", "")
                db_password = data.get("db_password", "")
                db_prefix = data.get("db_prefix", "lmoadll_")

                # 验证PostgreSQL参数
                if not db_name or not db_user:
                    return jsonify(
                        {
                            "success": False,
                            "message": "PostgreSQL数据库名称和用户名不能为空",
                        }
                    )

                # 注册PostgreSQL数据库
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

                # 获取数据库连接
                db = db_orm.get_db()
                db.connect()

                try:
                    # 设置表名
                    UserModel.set_table_name(f"{db_prefix}users")
                    OptionModel.set_table_name(f"{db_prefix}options")

                    # 保存网站配置
                    OptionModel.create(db, name="site_name", user=0, value=site_name)
                    OptionModel.create(db, name="site_url", user=0, value=site_url)

                    # 检查超级管理员是否已存在
                    superadmins = UserModel.find(db, group="superadministrator")
                    if superadmins and len(superadmins) > 0:
                        return jsonify(
                            {"success": False, "message": "超级管理员账号已存在"}
                        )

                    # 创建超级管理员账号
                    import time

                    current_time = int(time.time())

                    UserModel.create(
                        db,
                        name=superadministrator_username,
                        password=hashed_password,
                        mail=superadministrator_email,
                        createdAt=current_time,
                        isActive=1,
                        group="superadministrator",
                    )

                    db.commit()
                except Exception as e:
                    db.rollback()
                    return jsonify(
                        {"success": False, "message": f"创建管理员账号失败: {str(e)}"}
                    )
                finally:
                    db.disconnect()
            else:
                return jsonify(
                    {"success": False, "message": f"不支持的数据库类型: {db_type}"}
                )

            # 关闭安装模式
            WriteConfigToml("server", "install", False)

            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "message": f"创建管理员账号失败: {str(e)}"})
