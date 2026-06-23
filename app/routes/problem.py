"""题目路由：浏览 / 详情。"""
from flask import Blueprint, render_template, session

from app.models import Problem, Submission, User
from app.utils.decorators import login_required

problem_bp = Blueprint("problem", __name__, url_prefix="/problems")


@problem_bp.route("/")
@login_required
def list_problems():
    """题目列表页。教师看到管理入口 + 统计数据。"""
    problems = Problem.query.order_by(Problem.id).all()
    is_teacher = session.get("role") == "teacher"

    teacher_stats = None
    if is_teacher:
        teacher_stats = {
            "problem_count": Problem.query.count(),
            "submission_count": Submission.query.count(),
            "student_count": User.query.filter_by(role="student").count(),
            "pass_count": Submission.query.filter_by(status="pass").count(),
        }

    return render_template("problems.html",
                           problems=problems,
                           is_teacher=is_teacher,
                           teacher_stats=teacher_stats)


@problem_bp.route("/<int:problem_id>")
@login_required
def problem_detail(problem_id: int):
    """题目详情 + 编程 IDE 页。"""
    problem = Problem.query.get_or_404(problem_id)
    return render_template("editor.html", problem=problem)
