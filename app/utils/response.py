from flask import jsonify, Response
from typing import Any


def success_response(data: Any = None, msg: str = "ok", code: int = 0) -> tuple[Response, int]:
    return jsonify({"code": code, "msg": msg, "data": data}), 200


def error_response(msg: str, status_code: int = 400, code: int = 1) -> tuple[Response, int]:
    return jsonify({"code": code, "msg": msg, "data": None}), status_code


def handle_404_error(e: Any) -> tuple[Response, int]:
    return error_response("请求的资源不存在", 404)


def handle_405_error(e: Any) -> tuple[Response, int]:
    return error_response("请求方法不允许", 405)


def handle_400_error(e: Any) -> tuple[Response, int]:
    description = getattr(e, "description", "请求参数错误")
    return error_response(description, 400)


def handle_401_error(e: Any) -> tuple[Response, int]:
    description = getattr(e, "description", "未授权访问")
    return error_response(description, 401)


def handle_403_error(e: Any) -> tuple[Response, int]:
    description = getattr(e, "description", "权限不足")
    return error_response(description, 403)


def handle_500_error(e: Any) -> tuple[Response, int]:
    return error_response("服务器内部错误", 500)


def register_error_handlers(app: Any) -> None:
    app.register_error_handler(400, handle_400_error)
    app.register_error_handler(401, handle_401_error)
    app.register_error_handler(403, handle_403_error)
    app.register_error_handler(404, handle_404_error)
    app.register_error_handler(405, handle_405_error)
    app.register_error_handler(500, handle_500_error)
