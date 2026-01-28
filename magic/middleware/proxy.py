# -*- coding: utf-8 -*-
"""代理头处理中间件"""


def setup_proxy_fix_middleware(app):
    """设置代理头处理中间件"""
    original_asgi_app = app.asgi_app

    async def proxy_fix_middleware(scope, receive, send):
        if scope.get("type") == "http":
            client_addr = scope.get("client")
            client_host = client_addr[0] if client_addr else None

            if client_host in ("127.0.0.1", "localhost", "::1"):
                headers = dict(scope.get("headers", []))

                if b"x-forwarded-proto" in headers:
                    x_forwarded_proto = headers[b"x-forwarded-proto"].decode("latin1").strip()
                    if x_forwarded_proto in {"http", "https", "ws", "wss"}:
                        if scope.get("type") == "websocket":
                            scope["scheme"] = x_forwarded_proto.replace("http", "ws")
                        else:
                            scope["scheme"] = x_forwarded_proto

                if b"x-forwarded-for" in headers:
                    x_forwarded_for = headers[b"x-forwarded-for"].decode("latin1")
                    if x_forwarded_for:
                        hosts = [h.strip() for h in x_forwarded_for.split(",")]
                        if hosts:
                            for host in reversed(hosts):
                                if host not in ("127.0.0.1", "localhost", "::1"):
                                    scope["client"] = (host, 0)
                                    break

        await original_asgi_app(scope, receive, send)

    app.asgi_app = proxy_fix_middleware
