import jwt
import datetime
from functools import wraps
from flask import request, g
from typing import Callable, Any

from app.config import Config
from app.models.dataclasses import Role
from app.utils.response import error_response


def generate_token(user_id: str, role: Role) -> str:
    payload = {
        "user_id": user_id,
        "role": role.value,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=Config.JWT_EXPIRE_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_admin(username: str, password: str) -> bool:
    return username == Config.ADMIN_USER and password == Config.ADMIN_PASS


def require_auth(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return error_response("缺少认证令牌", 401)

        token = auth_header.split(" ")[1]
        payload = decode_token(token)
        if not payload:
            return error_response("认证令牌无效或已过期", 401)

        g.user_id = payload.get("user_id")
        g.user_role = payload.get("role")
        return f(*args, **kwargs)

    return decorated


def require_role(*roles: Role) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        @require_auth
        def decorated(*args: Any, **kwargs: Any) -> Any:
            user_role = g.get("user_role")
            if not user_role or user_role not in [r.value for r in roles]:
                return error_response("权限不足", 403)
            return f(*args, **kwargs)

        return decorated

    return decorator


def require_student(f: Callable[..., Any]) -> Callable[..., Any]:
    return require_role(Role.STUDENT)(f)


def require_teacher(f: Callable[..., Any]) -> Callable[..., Any]:
    return require_role(Role.TEACHER)(f)


def require_admin(f: Callable[..., Any]) -> Callable[..., Any]:
    return require_role(Role.ADMIN)(f)


def generate_student_token(student_id: str) -> str:
    return generate_token(student_id, Role.STUDENT)


def generate_teacher_token(teacher_id: str) -> str:
    return generate_token(teacher_id, Role.TEACHER)


def generate_admin_token(admin_id: str = "admin") -> str:
    return generate_token(admin_id, Role.ADMIN)
