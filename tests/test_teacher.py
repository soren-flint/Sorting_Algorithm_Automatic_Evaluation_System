"""测试教师路由：题目 CRUD。"""
import re

import pytest

from app.extensions import db
from app.models import Problem, TestCase, User


def _extract_csrf(html: str) -> str:
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return m.group(1) if m else ""


class TestTeacherProblemCRUD:
    """教师题目管理测试。"""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.client = app.test_client()
        with app.app_context():
            teacher = User(username="tcrud", role="teacher")
            teacher.set_password("123456")
            db.session.add(teacher)
            db.session.commit()

    def _login_teacher(self):
        resp = self.client.get("/auth/login")
        csrf = _extract_csrf(resp.data.decode())
        self.client.post("/auth/login", data={
            "username": "tcrud", "password": "123456", "csrf_token": csrf,
        })

    def test_manage_problems_page(self):
        self._login_teacher()
        resp = self.client.get("/teacher/problems")
        assert resp.status_code == 200

    def test_create_problem_page(self):
        self._login_teacher()
        resp = self.client.get("/teacher/problems/new")
        assert resp.status_code == 200

    def test_create_problem_basic(self):
        self._login_teacher()
        csrf = _extract_csrf(
            self.client.get("/teacher/problems/new").data.decode()
        )
        resp = self.client.post("/teacher/problems/new", data={
            "csrf_token": csrf,
            "title": "测试冒泡排序",
            "description": "实现冒泡排序",
            "difficulty": "easy",
            "algo_type": "bubble",
            "sort_rule": "strict",
            "complexity_ceiling": "",
            "tc_input": ["[5,2,8,1,3]", "[1]"],
            "tc_expected": ["[1,2,3,5,8]", "[1]"],
            "tc_public": ["1", "1"],
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"\xe5\x88\x9b\xe5\xbb\xba\xe6\x88\x90\xe5\x8a\x9f" in resp.data

    def test_create_problem_no_tests(self):
        self._login_teacher()
        csrf = _extract_csrf(
            self.client.get("/teacher/problems/new").data.decode()
        )
        resp = self.client.post("/teacher/problems/new", data={
            "csrf_token": csrf,
            "title": "无测试用例的题",
            "description": "",
            "difficulty": "medium",
            "algo_type": "any",
            "sort_rule": "strict",
            "complexity_ceiling": "",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_edit_problem_page(self):
        self._login_teacher()
        # 先创建
        csrf1 = _extract_csrf(
            self.client.get("/teacher/problems/new").data.decode()
        )
        self.client.post("/teacher/problems/new", data={
            "csrf_token": csrf1,
            "title": "待编辑的题",
            "description": "",
            "difficulty": "easy",
            "algo_type": "any",
            "sort_rule": "strict",
            "complexity_ceiling": "",
            "tc_input": ["[1,2]"],
            "tc_expected": ["[1,2]"],
            "tc_public": ["1"],
        })
        with self.app.app_context():
            p = Problem.query.filter_by(title="待编辑的题").first()
            pid = p.id
        resp = self.client.get(f"/teacher/problems/{pid}/edit")
        assert resp.status_code == 200

    def test_edit_problem_submit(self):
        self._login_teacher()
        csrf1 = _extract_csrf(
            self.client.get("/teacher/problems/new").data.decode()
        )
        self.client.post("/teacher/problems/new", data={
            "csrf_token": csrf1,
            "title": "旧标题", "description": "旧描述",
            "difficulty": "easy", "algo_type": "any",
            "sort_rule": "strict", "complexity_ceiling": "",
        })
        with self.app.app_context():
            p = Problem.query.filter_by(title="旧标题").first()
            pid = p.id
        csrf2 = _extract_csrf(
            self.client.get(f"/teacher/problems/{pid}/edit").data.decode()
        )
        resp = self.client.post(f"/teacher/problems/{pid}/edit", data={
            "csrf_token": csrf2,
            "title": "新标题", "description": "新描述",
            "difficulty": "hard", "algo_type": "quick",
            "sort_rule": "stalin", "complexity_ceiling": "O(n log n)",
            "tc_input": ["[3,1,2]"], "tc_expected": ["[1,2,3]"],
            "tc_public": ["1"],
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"\xe5\xb7\xb2\xe6\x9b\xb4\xe6\x96\xb0" in resp.data

    def test_delete_problem(self):
        self._login_teacher()
        csrf1 = _extract_csrf(
            self.client.get("/teacher/problems/new").data.decode()
        )
        self.client.post("/teacher/problems/new", data={
            "csrf_token": csrf1,
            "title": "待删除", "description": "",
            "difficulty": "easy", "algo_type": "any",
            "sort_rule": "strict", "complexity_ceiling": "",
        })
        with self.app.app_context():
            p = Problem.query.filter_by(title="待删除").first()
            pid = p.id
        csrf2 = _extract_csrf(
            self.client.get(f"/teacher/problems/{pid}/edit").data.decode()
        )
        resp = self.client.post(f"/teacher/problems/{pid}/delete", data={
            "csrf_token": csrf2,
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"\xe5\xb7\xb2\xe5\x88\xa0\xe9\x99\xa4" in resp.data

    def test_student_cannot_create(self):
        with self.app.app_context():
            s = User(username="student_x", role="student")
            s.set_password("123456")
            db.session.add(s)
            db.session.commit()
        resp = self.client.get("/auth/login")
        csrf = _extract_csrf(resp.data.decode())
        self.client.post("/auth/login", data={
            "username": "student_x", "password": "123456", "csrf_token": csrf,
        })
        resp = self.client.get("/teacher/problems/new")
        assert resp.status_code == 403
