# -*- coding: utf-8 -*-
from quart import Quart, jsonify, Response, request
from typing import Any
from magic.utils.log3 import logger


class APIException(Exception):
    """自定义业务异常"""
    def __init__(self, message: str, code: int = 233, data: Any = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data

class ResponseManager:
    def __init__(self, app: Quart | None = None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Quart):
        app.register_error_handler(APIException, self._handle_api_exception)
        app.register_error_handler(Exception, self._handle_generic_exception)
        app.after_request(self._format_response)

    async def _handle_api_exception(self, e: APIException):
        """处理已知的业务错误"""
        logger.warning(f"{request.scheme} {request.method} {request.remote_addr} {request.path} - {e.message}")
        return jsonify({"code": e.code, "msg": e.message, "data": e.data}), 200

    async def _handle_generic_exception(self, e: Exception):
        """处理未知的系统错误"""
        logger.error(f"{request.scheme} {request.method} {request.remote_addr} {request.path}", exc_info=True)
        return jsonify({"code": 500, "msg": "服务器内部错误"}), 500

    async def _format_response(self, response: Response) -> Response:
        """记录请求并统一响应格式"""
        logger.info(f"{response.status_code} {request.scheme} {request.method} {request.remote_addr} {request.path}")
        
        if response.status_code == 200 and response.is_json:
            data = await response.get_json()
            
            if not (isinstance(data, dict) and "code" in data):
                new_payload = {
                    "code": 200,
                    "msg": "OK",
                    "data": data
                }
                
                new_json_res = jsonify(new_payload)
                data_bytes = await new_json_res.get_data()
                response.set_data(data_bytes)
                
        return response

response_manager = ResponseManager()
