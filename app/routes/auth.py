"""认证路由：登录 / 注册 / 登出。"""
import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import User
from app.utils.decorators import login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# 用户名规则：3-20 位字母数字下划线
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")
# 密码最小长度
_MIN_PASSWORD_LEN = 4


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """用户注册。"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")

        # 校验
        errors = []
        if not username:
            errors.append("用户名不能为空")
        elif not _USERNAME_RE.match(username):
            errors.append("用户名需 3-20 位，仅允许字母、数字、下划线")
        if not password:
            errors.append("密码不能为空")
        elif len(password) < _MIN_PASSWORD_LEN:
            errors.append(f"密码至少 {_MIN_PASSWORD_LEN} 位")
        if role not in ("student", "teacher"):
            errors.append("角色无效")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("login.html", mode="register")

        if User.query.filter_by(username=username).first():
            flash("用户名已存在", "warning")
            return render_template("login.html", mode="register")

        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("注册成功，请登录", "success")
        return redirect(url_for("auth.login"))

    return render_template("login.html", mode="register")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """用户登录。"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("用户名和密码不能为空", "danger")
            return render_template("login.html", mode="login")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            flash(f"欢迎回来，{user.username}！", "success")

            # 教师登录后进管理面板
            if user.role == "teacher":
                return redirect(url_for("teacher.dashboard"))
            return redirect(url_for("problem.list_problems"))

        flash("用户名或密码错误", "danger")

    return render_template("login.html", mode="login")


@auth_bp.route("/logout")
@login_required
def logout():
    """登出。"""
    session.clear()
    flash("已登出", "info")
    return redirect(url_for("auth.login"))
