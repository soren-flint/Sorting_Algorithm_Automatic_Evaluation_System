"""测试可视化 API 和页面。"""
import json

import pytest

from app import create_app
from app.extensions import db
from app.models import Problem, SortStep, Submission, SubmissionDetail, TestCase, User


class TestVisualizationAPI:
    """可视化 API 测试。"""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.client = app.test_client()
        with app.app_context():
            # 创建用户 + 题目 + 提交 + detail + steps
            u = User(username="vizuser", role="student")
            u.set_password("123456")
            db.session.add(u)
            db.session.flush()

            p = Problem(title="可视化测试", difficulty="easy",
                        algo_type="bubble", sort_rule="strict", created_by=u.id)
            db.session.add(p)
            db.session.flush()

            tc = TestCase(problem_id=p.id, input_data="[3,1,2]",
                          expected_output="[1,2,3]")
            db.session.add(tc)
            db.session.flush()

            sub = Submission(user_id=u.id, problem_id=p.id,
                             code="def sort(a): return sorted(a)",
                             status="pass", score=100)
            db.session.add(sub)
            db.session.flush()

            detail = SubmissionDetail(submission_id=sub.id, test_case_id=tc.id,
                                      input_arr="[3,1,2]", actual_output="[1,2,3]",
                                      passed=True)
            db.session.add(detail)
            db.session.flush()

            # 模拟步骤数据
            for seq, arr in enumerate([[3,1,2], [1,3,2], [1,2,3]]):
                step = SortStep(detail_id=detail.id, seq=seq,
                                array_state=json.dumps(arr),
                                op="swap" if seq < 2 else "done",
                                i=0 if seq == 0 else None,
                                j=1 if seq == 0 else None)
                db.session.add(step)

            db.session.commit()
            self.submission_id = sub.id
            self.detail_id = detail.id

    def _login(self):
        resp = self.client.get("/auth/login")
        import re
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', resp.data.decode())
        token = csrf.group(1) if csrf else ""
        self.client.post("/auth/login", data={
            "username": "vizuser", "password": "123456", "csrf_token": token,
        })

    def test_steps_api_returns_data(self):
        """API 应返回步骤 JSON 数组。"""
        self._login()
        resp = self.client.get(f"/submit/api/steps/{self.detail_id}")
        assert resp.status_code == 200
        data = resp.json
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["op"] == "swap"
        assert data[0]["array_state"] == [3, 1, 2]

    def test_steps_api_has_required_fields(self):
        """每条步骤应包含必要字段。"""
        self._login()
        resp = self.client.get(f"/submit/api/steps/{self.detail_id}")
        data = resp.json
        for step in data:
            assert "seq" in step
            assert "array_state" in step
            assert "op" in step
            assert "i" in step
            assert "j" in step
            assert "note" in step
            assert "highlight_line" in step  # 策略C 新增
            assert "round" in step           # 策略C 新增

    def test_visualize_page_loads(self):
        """可视化页面可正常加载（DOM bar 模式，不再用 canvas）。"""
        self._login()
        resp = self.client.get(f"/submit/visualize/{self.submission_id}")
        assert resp.status_code == 200
        # 新版本使用 DOM bar 渲染，检查关键元素
        assert b"vizBarContainer" in resp.data  # 图表容器
        assert b"viz-bar-pillar" in resp.data   # DOM 柱状条

    def test_steps_api_empty_detail(self):
        """无步骤的 detail 应返回空数组。"""
        self._login()
        resp = self.client.get("/submit/api/steps/99999")
        assert resp.status_code == 200
        data = resp.json
        assert isinstance(data, list)
        assert len(data) == 0

    def test_submit_response_includes_detail_ids(self):
        """提交响应应包含 detail_ids。"""
        self._login()
        # 获取题目页的 CSRF
        resp = self.client.get("/problems/1")
        import re
        csrf = re.search(r'id="csrf-token" value="([^"]+)"', resp.data.decode())
        token = csrf.group(1) if csrf else ""

        code = "def sort(arr):\n    arr.sort()\n    return arr"
        resp = self.client.post("/submit/1", data={
            "code": code, "csrf_token": token,
        })
        assert resp.status_code == 200
        data = resp.json
        assert "detail_ids" in data
        assert isinstance(data["detail_ids"], list)
