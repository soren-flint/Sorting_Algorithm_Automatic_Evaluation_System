"""测试认证路由：注册 / 登录 / 登出。"""
import re

import pytest

from app import create_app
from app.extensions import db
from app.models import User


def _extract_csrf(html: str) -> str:
    """从 HTML 中提取 CSRF token。"""
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return m.group(1) if m else ""


class TestAuthRoutes:
    """认证功能端到端测试。"""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db
        self.client = app.test_client()

    def _create_user(self, username="testuser", password="123456", role="student"):
        with self.app.app_context():
            u = User(username=username, role=role)
            u.set_password(password)
            self.db.session.add(u)
            self.db.session.commit()

    def test_login_page_loads(self):
        resp = self.client.get("/auth/login")
        assert resp.status_code == 200
        assert b"\xe7\x99\xbb\xe5\xbd\x95" in resp.data  # 登录

    def test_register_page_loads(self):
        resp = self.client.get("/auth/register")
        assert resp.status_code == 200

    def test_login_success(self):
        self._create_user()
        resp = self.client.get("/auth/login")
        csrf = _extract_csrf(resp.data.decode())
        resp = self.client.post("/auth/login", data={
            "username": "testuser", "password": "123456", "csrf_token": csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_wrong_password(self):
        self._create_user()
        resp = self.client.get("/auth/login")
        csrf = _extract_csrf(resp.data.decode())
        resp = self.client.post("/auth/login", data={
            "username": "testuser", "password": "wrong", "csrf_token": csrf,
        })
        assert resp.status_code == 200
        assert b"\xe9\x94\x99\xe8\xaf\xaf" in resp.data  # 错误

    def test_register_new_user(self):
        resp = self.client.get("/auth/register")
        csrf = _extract_csrf(resp.data.decode())
        resp = self.client.post("/auth/register", data={
            "username": "newstudent", "password": "123456",
            "role": "student", "csrf_token": csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"\xe6\xb3\xa8\xe5\x86\x8c\xe6\x88\x90\xe5\x8a\x9f" in resp.data

    def test_register_duplicate_username(self):
        self._create_user()  # 先创建一个
        resp = self.client.get("/auth/register")
        csrf = _extract_csrf(resp.data.decode())
        resp = self.client.post("/auth/register", data={
            "username": "testuser", "password": "123456",
            "role": "student", "csrf_token": csrf,
        })
        assert b"\xe5\xb7\xb2\xe5\xad\x98\xe5\x9c\xa8" in resp.data

    def test_register_weak_password(self):
        resp = self.client.get("/auth/register")
        csrf = _extract_csrf(resp.data.decode())
        resp = self.client.post("/auth/register", data={
            "username": "newuser2", "password": "ab",
            "role": "student", "csrf_token": csrf,
        })
        assert resp.status_code == 200

    def test_register_invalid_username(self):
        resp = self.client.get("/auth/register")
        csrf = _extract_csrf(resp.data.decode())
        resp = self.client.post("/auth/register", data={
            "username": "ab", "password": "123456",
            "role": "student", "csrf_token": csrf,
        })
        assert resp.status_code == 200

    def test_logout(self):
        self._create_user()
        resp = self.client.get("/auth/login")
        csrf = _extract_csrf(resp.data.decode())
        self.client.post("/auth/login", data={
            "username": "testuser", "password": "123456", "csrf_token": csrf,
        })
        resp = self.client.get("/auth/logout", follow_redirects=True)
        assert resp.status_code == 200

    def test_protected_route_redirects(self):
        resp = self.client.get("/problems/", follow_redirects=True)
        assert resp.status_code == 200
        assert b"\xe7\x99\xbb\xe5\xbd\x95" in resp.data

    def test_teacher_access_blocked_for_student(self):
        self._create_user()
        resp = self.client.get("/auth/login")
        csrf = _extract_csrf(resp.data.decode())
        self.client.post("/auth/login", data={
            "username": "testuser", "password": "123456", "csrf_token": csrf,
        })
        resp = self.client.get("/teacher/")
        assert resp.status_code == 403
