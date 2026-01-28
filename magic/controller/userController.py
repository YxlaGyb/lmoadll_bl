# -*- coding: utf-8 -*-
import time
import logging
import random
import string
from magic.models.user import User
from quart import request, jsonify
from cachetools import TTLCache
from magic.utils.validate import isValidName, isValidPassword, isValidEmail
from magic.utils.cookies import setCookieToken
from magic.utils.Argon2Password import hashPassword
from magic.utils.Mail import sendMailAsync
from magic.service.userService import UserService
from magic.middleware.response import APIException
from magic.middleware.auth import AuthMiddleware, getCurrentUser


CODEEXPIRATIONTIME = 300
verification_codes = TTLCache(maxsize=1000000, ttl=CODEEXPIRATIONTIME) # {email: {"code": 验证码, "hash": 验证码哈希, "expiresAt": 过期时间戳}}

def verifyCode(email: str, code: str, codeSalt: str) -> tuple[bool, str | None]:
    """验证验证码是否有效"""

    code_data = verification_codes.get(email)
    if not code_data:
        return False, "验证码不存在或已过期喵喵"
    if code != code_data['code']:
        return False, "验证码错误喵喵"
    if code_data['hash'] != codeSalt:
        return False, "验证码哈希不匹配喵喵"
    del verification_codes[email]
    return True, None


class UserController:
    @staticmethod
    async def login():
        data = await request.get_json()
        email, password = (data["email"], data["password"])

        if not isValidEmail(email) or not isValidPassword(password):
            raise APIException("邮箱或密码格式不正确喵", code=233)

        result = await UserService.loginUser(email, password)
        if isinstance(result, int):
            raise APIException(f"{result}", code=500)
        payload = {
            "user_info": "登录成功喵"
        }
        response = jsonify(payload) 
        setCookieToken(response, result["token"])
        print(result)
        return response
    
    @staticmethod
    async def register():
        data = await request.get_json()
        if not isValidEmail(data["email"]) or not isValidName(data["username"]) or not isValidPassword(data["password"]):
            raise APIException("用户名或密码格式不正确喵", code=233)
        if len(data["username"]) < 2 or len(data["username"]) > 50:
            raise APIException("用户名长度应在2-50个字符之间喵喵", code=233)
        if len(data["password"]) < 8:
            raise APIException("密码长度应不少于8个字符喵喵", code=233)
        if len(data["code"]) != 6:
            raise APIException("验证码应为6位字母+数字喵喵", code=233)
        if await UserService.getUserByEmail(data["email"]):
            raise APIException("该邮箱已被注册喵喵", code=233)
        is_valid, error_message = verifyCode(data["email"], data["code"], data["codeSalt"])
        if not is_valid:
            raise APIException(error_message or "验证码验证失败喵喵", code=233)
        
        passwordHash = hashPassword(data["password"])
        if not passwordHash:
            raise APIException("密码哈希处理失败喵喵", code=500)
        clientIp = request.remote_addr or ""
        
        await UserService.createUser(
            name=data["username"],
            email=data["email"],
            password=passwordHash,
            ip=clientIp
        )

        result = await UserService.loginUser(data["email"], data["password"])
        if isinstance(result, int):
            raise APIException(f"{result}", code=500)
        tokenResult = result["token"]
        payload = {}
        response = jsonify(payload)
        setCookieToken(response, tokenResult)
        return {"message": "注册成功喵"}

    @staticmethod    
    async def sendEmailCodeRegister():
        data = await request.get_json()

        if not isValidEmail(data["email"]):
            raise APIException("邮箱格式错误喵", code=233)
        if await UserService.getUserByEmail(data["email"]):
            raise APIException("您的邮箱已经被使用了喵, 请换一个试试喵", code=233)

        code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        codeSalt = hashPassword(code)
        if not codeSalt:
            logging.error("验证码哈希失败")
            raise APIException("验证码生成失败喵喵", code=500)
        
        htmlContent = f"""
        <div style="font-family: sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 8px;">
            <h2 style="color: #333;">✨ 注册验证码待查收</h2>
            <p>您的验证码是 <b style="font-size: 24px; color: #007bff;">{code}</b></p>
            <p style="color: #666;">请在 {CODEEXPIRATIONTIME // 60} 分钟内完成验证，请勿泄露喵~</p>
            <hr style="border: none; border-top: 1px solid #eee;">
            <footer style="font-size: 12px; color: #999;">来自：数数洞洞平台</footer>
        </div>
        """

        mailSent = await sendMailAsync("注册验证码", [data["email"]], htmlContent)
        if not mailSent:
            raise APIException("邮件服务连接超时, 请稍后再试喵喵", code=500)

        expiresAt = int(time.time()) + CODEEXPIRATIONTIME
        verification_codes[data["email"]] = {
            "code": code,
            "hash": codeSalt,
            "createdAt": int(time.time()),
            "expiresAt": expiresAt
        }
        print(f"验证码 {code} 已成功生成并存储到内存中, 过期时间为 {expiresAt}")
        return {"codeSalt": codeSalt}
    
    @staticmethod
    @AuthMiddleware()
    async def getUserProfile():
        """获取用户信息"""
        user = await getCurrentUser()
        print(user)
        return jsonify({"code": 200, "data": "xxx"})
    
    @staticmethod
    @AuthMiddleware()
    async def getUserByUsername():
        """查询用户列表"""
        name = request.args.get("name", "")
        exactly = request.args.get("exactly", "")
        if not name.strip():
            raise APIException("用户名不能为空喵", code=233)
        if exactly == '1':
            user = await UserService.getUserByUsernameExactly(name)
        else:
            user = await UserService.getUserByUsername(name)
        return jsonify({
            "code": 200,
            "data": user
        })
    
    @staticmethod
    @AuthMiddleware()
    async def updateUserRoles():
        pass
    
    @staticmethod
    @AuthMiddleware()
    async def createUser():
        """创建用户"""
        data = await request.get_json()
        if not isValidEmail(data.get("email")) or not isValidName(data.get("username")) or not isValidPassword(data.get("password")):
            raise APIException("参数格式不正确喵", code=233)
        
        passwordHash = hashPassword(data["password"])
        if not passwordHash:
            raise APIException("密码哈希处理失败喵喵", code=500)
        
        result = await UserService.createUser(
            name=data["username"],
            email=data["email"],
            password=passwordHash,
            ip=request.remote_addr or ""
        )
        return jsonify({"code": 200, "message": "用户创建成功喵喵", "data": {"uid": result.uid}})
    
    @staticmethod
    @AuthMiddleware()
    async def updateUser():
        """修改用户信息"""
        data = await request.get_json()
        if not data.get("uid"):
            raise APIException("用户ID不能为空喵", code=233)
        
        result = await UserService.updateUser(data["uid"], data)
        if not result:
            raise APIException("用户不存在或修改失败喵喵", code=500)
        return jsonify({"code": 200, "message": "用户信息修改成功喵喵"})
    
    @staticmethod
    @AuthMiddleware()
    async def deleteUser():
        """删除用户"""
        data = await request.get_json()
        if not data.get("uid"):
            raise APIException("用户ID不能为空喵", code=233)
        
        result = await UserService.deleteUser(data["uid"])
        if not result:
            raise APIException("用户不存在或删除失败喵喵", code=500)
        return jsonify({"code": 200, "message": "用户删除成功喵喵"})
