# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
响应处理模块

本模块提供统一的响应封装
- 200 - 成功响应
- 233 - 自定义错误响应（已知错误）
- 500 - 系统错误响应（未知错误）
"""
from flask import jsonify, Response
from functools import wraps
from collections.abc import Callable


JSONBase = str | int | float | bool | None
JSONType = JSONBase | dict[str, "JSONType"] | list["JSONType"]
ResponseDict = dict[str, JSONType]
ValidReturn = Response | tuple[Response, int] | JSONType | tuple[JSONType, int]


class ResponseHandler:
    def __init__(self) -> None:
        self.codes: dict[str, int] = {
            "ok": 200,
            "custom": 233,
            "error": 500
        }

    def _make_json(self, code: int, msg: str, data: JSONType = None):
        body: ResponseDict = {"code": code, "message": msg}
        if data is not None:
            body["data"] = data
        return body
        

    def success_response(self, message: str="OK", data: JSONType = None):
        return jsonify(self._make_json(self.codes["ok"], message, data))
    def custom_error_response(self, message: str="ERROR", data: JSONType = None):
        return jsonify(self._make_json(self.codes["custom"], message, data))
    def error_response(self, message: str="ERROR", data: JSONType = None):
        return jsonify(self._make_json(self.codes["error"], message, data))


    def response_middleware(self, func: Callable[..., ValidReturn]) -> Callable[..., ValidReturn]:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> ValidReturn:
            try:
                result: ValidReturn = func(*args, **kwargs)
                if isinstance(result, tuple) and len(result) == 2:
                    val: object = result[0]
                    status: object = result[1]
                    if status == self.codes["custom"]:
                        return self.custom_error_response(message=str(val))
                    if status == self.codes["ok"]:
                        return self.success_response(data=val if isinstance(val, (dict, list, str, int, float, bool)) else None)
                if isinstance(result, (dict, list)):
                    return self.success_response(data=result)
                return result
            except Exception as e:
                return self.error_response(message=str(e))
        return wrapper

response_handler = ResponseHandler()
