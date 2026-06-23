"""数据模型 —— 7 张表。"""
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    """用户表。"""
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student", index=True)  # student | teacher

    # 关系
    submissions = db.relationship("Submission", back_populates="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        """哈希并存储密码。"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """校验密码。"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


class Problem(db.Model):
    """题目表。"""
    __tablename__ = "problem"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    difficulty = db.Column(db.String(20), default="medium")  # easy | medium | hard
    algo_type = db.Column(db.String(50), default="any")      # bubble|select|insert|quick|merge|heap|any
    sort_rule = db.Column(db.String(20), default="strict")    # strict|stalin|stable|topk
    complexity_ceiling = db.Column(db.String(20), nullable=True)  # 如 O(n log n)，NULL 不设限
    example_code = db.Column(db.Text, default="")                   # 标准示例代码
    is_meme = db.Column(db.Boolean, default=False)                   # 整活题目标记
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # 关系
    test_cases = db.relationship("TestCase", back_populates="problem", lazy="dynamic",
                                 cascade="all, delete-orphan")
    submissions = db.relationship("Submission", back_populates="problem", lazy="dynamic")
    creator = db.relationship("User", backref="created_problems")

    def __repr__(self) -> str:
        return f"<Problem {self.title} [{self.algo_type}]>"


class TestCase(db.Model):
    """测试用例表。"""
    __tablename__ = "test_case"
    __test__ = False  # 避免 pytest 将其收集为测试类

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False, index=True)
    input_data = db.Column(db.Text, nullable=False)          # JSON 数组，如 [5,2,8,1,3]
    expected_output = db.Column(db.Text, nullable=True)       # strict 模式可空，按规则推导
    is_public = db.Column(db.Boolean, default=True)

    # 关系
    problem = db.relationship("Problem", back_populates="test_cases")
    submission_details = db.relationship("SubmissionDetail", back_populates="test_case",
                                         lazy="dynamic")

    def __repr__(self) -> str:
        return f"<TestCase pid={self.problem_id} input={self.input_data[:30]}>"


class Submission(db.Model):
    """提交记录表。"""
    __tablename__ = "submission"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False, index=True)
    code = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending", index=True)      # pending|pass|fail|error|timeout
    score = db.Column(db.Integer, default=0)
    recognized_algo = db.Column(db.String(50), nullable=True)  # 识别出的算法
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # 关系
    user = db.relationship("User", back_populates="submissions")
    problem = db.relationship("Problem", back_populates="submissions")
    details = db.relationship("SubmissionDetail", back_populates="submission", lazy="dynamic",
                              cascade="all, delete-orphan")
    complexity_analysis = db.relationship("ComplexityAnalysis", back_populates="submission",
                                          uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Submission uid={self.user_id} pid={self.problem_id} status={self.status}>"


class SubmissionDetail(db.Model):
    """评测详情表（每个测试用例一条）。"""
    __tablename__ = "submission_detail"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submission.id"), nullable=False, index=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey("test_case.id"), nullable=False, index=True)
    input_arr = db.Column(db.Text, nullable=True)       # 该用例输入数组 JSON
    actual_output = db.Column(db.Text, nullable=True)   # 学生代码实际输出
    passed = db.Column(db.Boolean, default=False)
    feedback = db.Column(db.Text, nullable=True)         # 智能反馈文本

    # 关系
    submission = db.relationship("Submission", back_populates="details")
    test_case = db.relationship("TestCase", back_populates="submission_details")
    sort_steps = db.relationship("SortStep", back_populates="detail", lazy="dynamic",
                                 cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SubmissionDetail sid={self.submission_id} passed={self.passed}>"


class SortStep(db.Model):
    """排序步骤表（可视化数据源·工程冗余核心）。"""
    __tablename__ = "sort_step"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    detail_id = db.Column(db.Integer, db.ForeignKey("submission_detail.id"), nullable=False, index=True)
    seq = db.Column(db.Integer, nullable=False, index=True)          # 步骤序号
    array_state = db.Column(db.Text, nullable=False)      # 数组快照 JSON
    op = db.Column(db.String(20), nullable=False)         # compare|swap|set|delete|done|error
    i = db.Column(db.Integer, nullable=True)              # 操作下标 i
    j = db.Column(db.Integer, nullable=True)              # 操作下标 j
    note = db.Column(db.Text, nullable=True)              # 可选备注
    highlight_line = db.Column(db.Integer, nullable=True)  # 对应用户代码行号（策略C）
    round_num = db.Column(db.Integer, nullable=True)       # 轮次（外层循环计数）

    # 关系
    detail = db.relationship("SubmissionDetail", back_populates="sort_steps")

    def __repr__(self) -> str:
        return f"<SortStep seq={self.seq} op={self.op}>"


class ComplexityAnalysis(db.Model):
    """复杂度分析表（按需触发，不在常规评测链路）。"""
    __tablename__ = "complexity_analysis"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submission.id"), nullable=False, unique=True)
    estimated = db.Column(db.String(20), nullable=True)    # 估算结果，如 O(n²)
    theoretical = db.Column(db.String(20), nullable=True)  # 理论值，如 O(n²)
    timings = db.Column(db.Text, nullable=True)            # 各规模耗时 JSON
    ratio = db.Column(db.Float, nullable=True)             # 最大/次大规模耗时比
    meets_ceiling = db.Column(db.Boolean, nullable=True)   # 是否达到题目复杂度门槛
    analyzed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    submission = db.relationship("Submission", back_populates="complexity_analysis")

    def __repr__(self) -> str:
        return f"<ComplexityAnalysis sid={self.submission_id} est={self.estimated}>"
