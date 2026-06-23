"""教师路由：建题 CRUD / 查重 / 仪表盘统计。"""
import json

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.extensions import db
from sqlalchemy.orm import joinedload
from app.models import Problem, Submission, TestCase, User
from app.utils.decorators import login_required, teacher_required

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


# ═══ 仪表盘 ═══

@teacher_bp.route("/")
@login_required
@teacher_required
def dashboard():
    """教师仪表盘——统计概览。"""
    stats = {
        "problem_count": Problem.query.count(),
        "submission_count": Submission.query.count(),
        "student_count": User.query.filter_by(role="student").count(),
        "pass_count": Submission.query.filter_by(status="pass").count(),
    }
    recent_subs = (
        Submission.query
        .options(joinedload(Submission.user), joinedload(Submission.problem))
        .order_by(Submission.submitted_at.desc())
        .limit(10)
        .all()
    )
    return render_template("teacher/dashboard.html", stats=stats, recent_subs=recent_subs)


# ═══ 题目管理列表 ═══

@teacher_bp.route("/problems")
@login_required
@teacher_required
def manage_problems():
    """教师题目管理列表。"""
    problems = Problem.query.order_by(Problem.id).all()
    return render_template("teacher/manage_problems.html", problems=problems)


# ═══ 创建题目 ═══

@teacher_bp.route("/problems/new", methods=["GET", "POST"])
@login_required
@teacher_required
def create_problem():
    """教师创建新题目。"""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        difficulty = request.form.get("difficulty", "medium")
        algo_type = request.form.get("algo_type", "any")
        sort_rule = request.form.get("sort_rule", "strict")
        complexity_ceiling = request.form.get("complexity_ceiling") or None

        if not title:
            flash("题目标题不能为空", "danger")
            return render_template("teacher/create_problem.html")

        # 字段合法性校验
        VALID_DIFFICULTY = {"easy", "medium", "hard", "整活 🤪"}
        VALID_ALGO_TYPE = {"bubble", "select", "insert", "quick", "merge", "heap", "any"}
        VALID_SORT_RULE = {"strict", "stalin", "stable", "topk"}

        if difficulty not in VALID_DIFFICULTY:
            flash(f"无效难度: {difficulty}", "danger")
            return render_template("teacher/create_problem.html")
        if algo_type not in VALID_ALGO_TYPE:
            flash(f"无效算法类型: {algo_type}", "danger")
            return render_template("teacher/create_problem.html")
        if sort_rule not in VALID_SORT_RULE:
            flash(f"无效排序规则: {sort_rule}", "danger")
            return render_template("teacher/create_problem.html")

        problem = Problem(
            title=title,
            description=description,
            difficulty=difficulty,
            algo_type=algo_type,
            sort_rule=sort_rule,
            complexity_ceiling=complexity_ceiling,
            created_by=session["user_id"],
        )
        db.session.add(problem)
        db.session.flush()

        # 解析测试用例（支持多组）
        inputs = request.form.getlist("tc_input")
        expecteds = request.form.getlist("tc_expected")
        publics = request.form.getlist("tc_public")

        for i, inp in enumerate(inputs):
            inp = inp.strip()
            if not inp:
                continue
            # 验证 JSON 格式
            try:
                json.loads(inp)
            except (json.JSONDecodeError, ValueError):
                flash(f"测试用例 #{i + 1} 输入不是有效 JSON: {inp[:50]}", "danger")
                continue

            exp = expecteds[i].strip() if i < len(expecteds) else None
            if exp:
                try:
                    json.loads(exp)
                except (json.JSONDecodeError, ValueError):
                    exp = None  # 期望输出可选

            is_public = i < len(publics) and publics[i] == "1"

            tc = TestCase(
                problem_id=problem.id,
                input_data=inp,
                expected_output=exp if exp else None,
                is_public=is_public,
            )
            db.session.add(tc)

        db.session.commit()
        flash(f"题目「{title}」创建成功！", "success")
        return redirect(url_for("teacher.manage_problems"))

    return render_template("teacher/create_problem.html")


# ═══ 编辑题目 ═══

@teacher_bp.route("/problems/<int:problem_id>/edit", methods=["GET", "POST"])
@login_required
@teacher_required
def edit_problem(problem_id: int):
    """教师编辑题目。"""
    problem = Problem.query.get_or_404(problem_id)

    if request.method == "POST":
        problem.title = request.form.get("title", "").strip() or problem.title
        problem.description = request.form.get("description", "").strip()
        problem.difficulty = request.form.get("difficulty", problem.difficulty)
        problem.algo_type = request.form.get("algo_type", problem.algo_type)
        problem.sort_rule = request.form.get("sort_rule", problem.sort_rule)
        problem.complexity_ceiling = request.form.get("complexity_ceiling") or None

        # ── 先收集并校验所有新测试用例（不操作 DB）──
        inputs = request.form.getlist("tc_input")
        expecteds = request.form.getlist("tc_expected")
        publics = request.form.getlist("tc_public")

        new_cases: list[dict] = []
        for i, inp in enumerate(inputs):
            inp = inp.strip()
            if not inp:
                continue
            try:
                json.loads(inp)
            except (json.JSONDecodeError, ValueError):
                flash(f"测试用例 #{i + 1} 输入不是有效 JSON: {inp[:50]}", "danger")
                continue

            exp = expecteds[i].strip() if i < len(expecteds) else None
            if exp:
                try:
                    json.loads(exp)
                except (json.JSONDecodeError, ValueError):
                    exp = None

            is_public = i < len(publics) and publics[i] == "1"
            new_cases.append({
                "input_data": inp,
                "expected_output": exp if exp else None,
                "is_public": is_public,
            })

        # ── 原子操作：删旧 + 建新 + 提交（异常自动回滚）──
        try:
            TestCase.query.filter_by(problem_id=problem.id).delete()
            for nc in new_cases:
                tc = TestCase(
                    problem_id=problem.id,
                    input_data=nc["input_data"],
                    expected_output=nc["expected_output"],
                    is_public=nc["is_public"],
                )
                db.session.add(tc)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("题目更新失败，请重试", "danger")
            return render_template("teacher/edit_problem.html", problem=problem)

        flash(f"题目「{problem.title}」已更新", "success")
        return redirect(url_for("teacher.manage_problems"))

    return render_template("teacher/edit_problem.html", problem=problem)


# ═══ 删除题目 ═══

@teacher_bp.route("/problems/<int:problem_id>/delete", methods=["POST"])
@login_required
@teacher_required
def delete_problem(problem_id: int):
    """教师删除题目（级联删除所有关联数据）。"""
    problem = Problem.query.get_or_404(problem_id)
    title = problem.title

    # SQLAlchemy cascade 删除（模型已配置 cascade="all, delete-orphan"）
    # SQLite 外键约束已通过 PRAGMA foreign_keys=ON 启用
    db.session.delete(problem)
    db.session.commit()

    flash(f"题目「{title}」已删除", "info")
    return redirect(url_for("teacher.manage_problems"))


# ═══ 查重 ═══

@teacher_bp.route("/similarity", methods=["GET", "POST"])
@login_required
@teacher_required
def similarity_check():
    """代码查重页——选择题目，检测相似提交。"""
    from app.core.similarity import detect

    problems = Problem.query.order_by(Problem.id).all()
    results = None
    selected_problem = None

    if request.method == "POST":
        problem_id = request.form.get("problem_id", type=int)
        threshold = request.form.get("threshold", 0.85, type=float)
        selected_problem = Problem.query.get(problem_id)

        if selected_problem:
            subs = (
                Submission.query
                .options(joinedload(Submission.user))
                .filter_by(problem_id=problem_id)
                .filter(Submission.status == "pass")
                .all()
            )
            results = detect(subs, threshold=threshold)

    return render_template("teacher/similarity.html",
                           problems=problems, results=results,
                           selected_problem=selected_problem)
