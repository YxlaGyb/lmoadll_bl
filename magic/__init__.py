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
# from magic.utils.Mail import init_mail, load_matl_config
from magic.utils.log2 import logger, _is_reload  # noqa: F401
from magic.PluginSystem import init_plugin_system
from magic.utils.jwt import InitJwtManager
from magic.routes.routes import combine_routes
from magic.PluginSystem import get_plugin_manager
import logging
import os


async def Init_module(app: Quart) -> None:
    """初始化模块"""
    
    await check_config_file()
    plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'contents', 'plugin')
    plugin_manager = init_plugin_system(plugin_dir)
    plugin_manager.load_plugins()
    logging.info("插件系统初始化完成")

    # 简单的代理头处理中间件
    original_asgi_app = app.asgi_app
    
    async def proxy_fix_middleware(scope, receive, send):
        if scope.get("type") == "http":
            client_addr = scope.get("client")
            client_host = client_addr[0] if client_addr else None
            
            # 只信任本地回环地址
            if client_host in ("127.0.0.1", "localhost", "::1"):
                headers = dict(scope.get("headers", []))
                
                # 处理 X-Forwarded-Proto
                if b"x-forwarded-proto" in headers:
                    x_forwarded_proto = headers[b"x-forwarded-proto"].decode("latin1").strip()
                    if x_forwarded_proto in {"http", "https", "ws", "wss"}:
                        if scope.get("type") == "websocket":
                            scope["scheme"] = x_forwarded_proto.replace("http", "ws")
                        else:
                            scope["scheme"] = x_forwarded_proto
                
                # 处理 X-Forwarded-For
                if b"x-forwarded-for" in headers:
                    x_forwarded_for = headers[b"x-forwarded-for"].decode("latin1")
                    if x_forwarded_for:
                        hosts = [h.strip() for h in x_forwarded_for.split(",")]
                        if hosts:
                            # 使用第一个非信任主机的IP
                            for host in reversed(hosts):
                                if host not in ("127.0.0.1", "localhost", "::1"):
                                    scope["client"] = (host, 0)
                                    break
        
        await original_asgi_app(scope, receive, send)
    
    app.asgi_app = proxy_fix_middleware
    
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
    InitJwtManager(app)
    # load_matl_config()
    # init_mail(app)
    combine_routes(app)
