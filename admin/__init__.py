# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
系统后台管理

为了区分普通用户和管理员, 此管理面板为管理员专属;
"""

from functools import wraps
from quart import Blueprint, send_file, Response, redirect, url_for, request
from magic.utils.jwt import GetCurrentUserIdentity
from magic.utils.db import GetUserRoleByIdentity
import logging



admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """
    检查登录状态

    先检查用户是否登录, 如果用户未登录，重定向到登录页面
    如果用户是管理员, 则可以前往admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_identity = GetCurrentUserIdentity()
        if user_identity is None:
            original_path = request.path
            if request.query_string:
                original_path = f"{original_path}?{request.query_string.decode('utf-8')}"
            return redirect(url_for('login.login_page', redirect=original_path))
        
        try:
            user_group = GetUserRoleByIdentity(user_identity)
            
            # 检查返回结果类型
            if isinstance(user_group, list) and len(user_group) > 0 and not user_group[0]:
                # 如果是错误列表 [False, message]
                print(f"查询用户角色失败喵: {user_group[1]}")
                return redirect('/')

            if isinstance(user_group, tuple) and len(user_group) > 0:
                user_role = user_group[0]
                
                if user_role in ['superadministrator', 'administrator']:
                    return f(*args, **kwargs)
                else:
                    return redirect('/')
            else:
                return redirect('/')
                
        except Exception as e:
            logging.error(f"获取用户信息时出错喵: {e}")
            return redirect('/')
    
    return decorated_function


@admin_bp.route('/', methods=['GET'])
@admin_required
def admin_index() -> Response:
    return send_file('admin/base/admin.html')


@admin_bp.route('/options-general', methods=['GET'])
@admin_required
def admin_options_general() -> Response:
    return send_file('admin/base/options-general.html')


@admin_bp.route('/usermanagement', methods=['GET'])
@admin_required
def admin_usermange() -> Response:
    return send_file('admin/base/UserManagement.html')
