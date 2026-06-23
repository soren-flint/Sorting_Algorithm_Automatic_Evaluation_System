"""视图装饰器。"""
from functools import wraps

from flask import redirect, session, url_for


def login_required(f):
    """要求登录的装饰器。未登录重定向到登录页。"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def teacher_required(f):
    """要求教师角色的装饰器。"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "teacher":
            return "需要教师权限", 403
        return f(*args, **kwargs)
    return decorated
