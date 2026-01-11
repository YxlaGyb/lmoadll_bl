import random
import re
import string
import time
import logging
from quart import request, redirect, url_for
from quart_mail import Message
from functools import wraps
from magic.utils.Mail import mail, SMTP_CONFIG
from magic.utils.Argon2Password import VerifyPassword, HashPassword
from magic.utils.jwt import CreateTokens, GetCurrentUserIdentity
from magic.utils.TomlConfig import DoesitexistConfigToml
from magic.utils.db import db_orm, GetUserByEmail, GetDbConnection
from magic.utils.cookies import cookie_manager
from magic.PluginSystem import call_plugin_hook
from magic.middleware.response import response_handler


class UserController:
    
    @staticmethod
    @response_handler.response_middleware
    def login_api():
        data = request.get_json()
        if not data["username_email"] or not data["password"]:
            return response_handler.custom_error_response("邮箱和密码不能为空喵喵")
        
        user = GetUserByEmail(data["username_email"])
        if not user:
            return response_handler.custom_error_response("邮箱或密码错误喵喵")
        
        if not VerifyPassword(user['password'], data["password"]):
            return response_handler.custom_error_response("邮箱或密码错误喵喵")
        
        tokens = CreateTokens(identity=str(user['uid']))
        if not tokens:
            return response_handler.error_response("生成令牌失败喵喵")

        # access_token = tokens['lmoadllUser']
        refresh_token = tokens['lmoadll_refresh_token']

        response_data = {
            "uid": user['uid'],
            "name": user['name'],
            "avatar": "",
            "group": user['group']
        }
        response = response_handler.success_response(response_data, "登录成功喵")
        
        response = cookie_manager.set_refresh_token(response, refresh_token)
        
        # response = cookie_manager.set_access_token(response, access_token)

        try:
            db = db_orm.get_db("default")
            success, message, _, _, table_name = GetDbConnection("users")
            if success:
                current_time = int(time.time())  # 获取当前时间戳
                # 使用同一个连接执行更新操作
                db.execute(f"UPDATE {table_name} SET lastLogin = ? WHERE uid = ?", (current_time, user['uid']))
                db.commit()
        except Exception as e:
            logging.warning(f"更新用户最后登录时间失败喵: {e}")
        finally:
            # 确保连接被归还到连接池
            try:
                db_orm.return_db(db, "default")
            except:
                pass

        return response