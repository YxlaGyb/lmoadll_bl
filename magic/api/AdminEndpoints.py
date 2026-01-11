# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0

import logging
import json
from quart import Blueprint, Response, request
from admin import admin_required
from magic.utils.jwt import GetCurrentUserIdentity
from magic.utils.TomlConfig import DoesitexistConfigToml
from magic.utils.db import (
    GetUserRoleByIdentity,
    GetUserCount,
    GetUserNameByIdentity,
    GetSiteOptionByName,
    GetOrSetSiteOption,
    SearchUsers
)


admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/user_count', methods=['POST'])
@admin_required
def admin_get_user_count() -> Response:
    """get user count"""
    user_count = GetUserCount()
    return Response(str(user_count), mimetype='text/plain')


@admin_bp.route('/get_admin_name', methods=['POST'])
@admin_required
def admin_get_admin_name() -> Response:
    """get admin name"""
    user_identity = GetCurrentUserIdentity()
    if user_identity is None:
        return Response("Unknown", mimetype='text/plain')
    
    try:
        user_group = GetUserRoleByIdentity(user_identity)
        if user_group and user_group[0] in ['superadministrator', 'administrator']:
            user_name = GetUserNameByIdentity(user_identity)
            if user_name and user_name[0]:
                return Response(user_name[0], mimetype='text/plain')
        return Response("Unknown", mimetype='text/plain')
    except Exception as e:
        logging.error(f"获取用户信息时出错: {e}")
        return Response("Unknown", mimetype='text/plain')


@admin_bp.route('/get_admin_identity', methods=['POST'])
@admin_required
def admin_get_admin_identity() -> Response:
    """get admin Identity"""
    user_identity = GetCurrentUserIdentity()
    if user_identity is None:
        return Response("Unknown", mimetype='text/plain')
    
    try:
        user_group = GetUserRoleByIdentity(user_identity)
        if user_group and len(user_group) > 0:
            if user_group[0] == 'superadministrator':
                return Response('超级管理员', mimetype='text/plain')
            elif user_group[0] == 'administrator':
                return Response('管理员', mimetype='text/plain')
        return Response('Unknown', mimetype='text/plain')
    except Exception as e:
        logging.error(f"获取用户身份时出错: {e}")
        return Response('Unknown', mimetype='text/plain')


@admin_bp.route('/get_name_options', methods=['POST'])
@admin_required
def admin_get_name_options() -> Response:
    """get name options"""
    try:
        if request.json is None:
            return Response('', mimetype='text/plain')
        
        option_name = request.json.get('user', '').strip()
        name_options = GetSiteOptionByName(option_name) # [True, {"name": name, "user": user, "value": value}]
        if name_options[0] and name_options[1] is not None:
            return Response(name_options[1]['value'], mimetype='text/plain')
        else:
            return Response('', mimetype='text/plain')
    except Exception as e:
        logging.error(f'获取全局设置失败喵: {e}')
        return Response('Unknown', mimetype='text/plain')


@admin_bp.route('/users/search', methods=['GET'])
@admin_required
def admin_search_users() -> Response:
    """搜索用户API"""
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        return Response('{"users": []}', mimetype='application/json')
    try:
        results = SearchUsers(keyword)
        if isinstance(results, list) and results and isinstance(results[0], dict):
            return Response(json.dumps({"users": results}), mimetype='application/json')
        elif isinstance(results, list) and not results:
            return Response('{"users": []}', mimetype='application/json')
        else:
            return Response('{"users": []}', mimetype='application/json')
    except Exception as e:
        logging.error(f"搜索用户API出错: {e}")
        return Response('{"users": []}', mimetype='application/json')


@admin_bp.route('/set_name_options', methods=['POST'])
@admin_required
def admin_set_name_options() -> Response:
    """set name options"""
    try:
        if request.json is None:
            return Response("", mimetype='text/plain')
        site_name = request.json.get('site_name').strip()
        site_description = request.json.get('site_description').strip()
        site_keywords = request.json.get('site_keywords').strip()
        enable_registration = str(request.json.get('enable_registration')).lower()
        db_prefix = DoesitexistConfigToml("db", "sql_prefix")
        sql_sqlite_path = DoesitexistConfigToml("db", "sql_sqlite_path")

        if not db_prefix or not sql_sqlite_path:
            return Response("数据库配置缺失", mimetype='text/plain')

        # 保存网站名称
        result_name = GetOrSetSiteOption(db_prefix, sql_sqlite_path, 'site_name', site_name)
        # 保存网站描述
        result_description = GetOrSetSiteOption(db_prefix, sql_sqlite_path, 'site_description', site_description)
        # 保存网站关键词
        result_keywords = GetOrSetSiteOption(db_prefix, sql_sqlite_path, 'site_keywords', site_keywords)
        # 保存允许用户注册设置
        result_registration = GetOrSetSiteOption(db_prefix, sql_sqlite_path, 'enable_registration', enable_registration)
        
        if result_name[0] and result_description[0] and result_keywords[0] and result_registration[0]:
            return Response("网站设置保存成功", mimetype='text/plain')
        else:
            print(f'网站设置保存失败喵: {result_name[1]}, {result_description[1]}, {result_keywords[1]}, {result_registration[1]}')
            return Response(f"网站设置保存失败: {result_name[1]}, {result_description[1]}, {result_keywords[1]}, {result_registration[1]}", mimetype='text/plain')
    except Exception as e:
        logging.error(f'保存全局设置失败喵: {e}')
        return Response(f'保存全局设置失败: {e}', mimetype='text/plain')
