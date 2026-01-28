# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
主要的lmoadll的组件, 这是魔法()
"""

from quart import Quart
from quart_cors import cors
from magic.utils.TomlConfig import check_config_file
from magic.utils.log3 import logger  # noqa: F401
from magic.PluginSystem import init_plugin_system
from magic.routes.routes import combineRoutes
from magic.PluginSystem import get_plugin_manager
from magic.utils import jwt
from magic.utils.db.connection import init_db
from magic.service.rbac.initRBAC import initDefaultRbac
from magic.middleware.proxy import setup_proxy_fix_middleware
import logging
import os


async def Init_module(app: Quart) -> None:
    """初始化模块"""
    
    plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'contents', 'plugin')
    plugin_manager = init_plugin_system(plugin_dir)
    plugin_manager.load_plugins()
    logging.info("插件系统初始化完成")

    setup_proxy_fix_middleware(app)
    
    cors(app, allow_origin={r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": [],
            "max_age": 600
        }},
        allow_headers=["Content-Type","Authorization","X-Requested-With"],
        expose_headers=["X-RateLimit-Limit","X-RateLimit-Remaining","X-RateLimit-Reset"],
        max_age=600)

    plugin_manager = get_plugin_manager()
    plugin_manager.register_all_api_routes(app)
    await combineRoutes(app)
    init_db()
    await initDefaultRbac(app)
