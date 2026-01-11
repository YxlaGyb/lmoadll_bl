# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
管理员专属登录页面
"""

from quart import Blueprint, send_file, request, redirect
from magic.utils.jwt import GetCurrentUserIdentity


login_bp = Blueprint('login', __name__, url_prefix='/login')


@login_bp.route('/', methods=["GET"])
def login_page():
    """
    如果已经登录, 则重定向;
    否则返回登录页面, 让用户登录
    
    注意: GetCurrentUserIdentity 现在支持双Token系统, 会验证access token
    """
    user_identity = GetCurrentUserIdentity()
    if user_identity is None:
        return send_file('./admin/base/login.html')
    else:
        redirect_url = request.args.get('redirect', '/')
        return redirect(redirect_url)
