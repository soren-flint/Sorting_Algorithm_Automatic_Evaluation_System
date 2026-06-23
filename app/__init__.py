"""Flask 应用工厂。"""
import os
import secrets

from flask import Flask, abort, redirect, request, session, url_for

from app.config import Config
from app.extensions import db


def create_app(config_class=Config) -> Flask:
    """创建并配置 Flask 应用实例。"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # SQLite 并发优化：必须在 db.init_app 之前设置
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {
            "timeout": 15,
            "check_same_thread": False,
        },
    }

    # 初始化扩展
    db.init_app(app)

    # SQLite WAL 模式：允许读写并发
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        """对 SQLite 连接启用 WAL 日志模式 + 外键约束。"""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # --- CSRF 保护（轻量 session-based，不依赖 Flask-WTF）---
    @app.before_request
    def csrf_protect():
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            token = session.get("_csrf_token")
            if not token:
                token = secrets.token_hex(32)
                session["_csrf_token"] = token
            # 同时支持 form 数据和 AJAX 请求头两种 CSRF 传递方式
            req_token = request.form.get("csrf_token", "") or request.headers.get("X-CSRF-Token", "")
            if not secrets.compare_digest(token, req_token):
                return {"error": "CSRF token 验证失败，请刷新页面后重试"}, 400, {"Content-Type": "application/json"}

    def generate_csrf_token():
        if "_csrf_token" not in session:
            session["_csrf_token"] = secrets.token_hex(32)
        return session["_csrf_token"]

    app.jinja_env.globals["csrf_token"] = generate_csrf_token

    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.problem import problem_bp
    from app.routes.submit import submit_bp
    from app.routes.teacher import teacher_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(problem_bp)
    app.register_blueprint(submit_bp)
    app.register_blueprint(teacher_bp)

    # 首页重定向到题目列表
    @app.route("/")
    def index():
        return redirect(url_for("problem.list_problems"))

    # 确保 instance 目录存在并建表
    os.makedirs(app.instance_path, exist_ok=True)

    with app.app_context():
        from app import models  # noqa: F401  确保模型被导入
        db.create_all()

    return app