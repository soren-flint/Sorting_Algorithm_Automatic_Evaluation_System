"""提交与评测路由（核心）—— Phase 2 完整实现。"""
import ast
import json
import logging

from flask import Blueprint, abort, jsonify, render_template, request, session

from app.core.comparator import compare_outputs
from app.core.feedback import diagnose, static_check_sort
from app.core.grader import grade
from app.core.recognizer import recognize_algorithm
from app.core.sandbox import run_code
from app.core.step_collector import collect_steps
from app.core.algo_semantic_check import check_semantic
from app.extensions import db
from sqlalchemy.orm import joinedload
from app.models import Problem, SortStep, Submission, SubmissionDetail
from app.utils.decorators import login_required

submit_bp = Blueprint("submit", __name__, url_prefix="/submit")
logger = logging.getLogger(__name__)


@submit_bp.route("/<int:problem_id>", methods=["POST"])
@login_required
def submit_code(problem_id: int):
    """提交代码并执行完整评测流程。"""
    problem = Problem.query.get_or_404(problem_id)
    code = request.form.get("code", "").strip()

    if not code:
        return jsonify({"error": "代码不能为空"}), 400

    # --- 0. 一次性 AST 解析（后续所有模块复用，避免 14 次重复解析）---
    try:
        code_tree = ast.parse(code)
    except SyntaxError:
        code_tree = None  # 语法错误时后续函数自行处理

    # --- 1. AST 静态检查（先于沙箱，提前暴露安全问题）---
    static_issues = static_check_sort(code, tree=code_tree)
    if any(i["type"] == "安全警告" for i in static_issues):
        return jsonify({"error": "代码包含不允许的函数调用", "issues": static_issues}), 400

    # --- 2. 算法识别 ---
    recognized = recognize_algorithm(code, tree=code_tree)

    # --- 2b. 算法语义白盒校验 ---
    semantic_issues = check_semantic(code, recognized, tree=code_tree)
    # 将语义校验结果合并到 static_issues（扩充静态检查覆盖面）
    for si in semantic_issues:
        static_issues.append({
            "type": "语义校验",
            "line": si.get("line"),
            "hint": si["hint"],
            "severity": si.get("severity", "warning"),
        })

    # --- 3. 预计算代码行标记（多用例复用，避免每用例重复 AST 解析）---
    algo_key_marker = recognized.split("(")[0].strip().lower() if "(" in recognized else recognized.strip().lower()
    marker_result = None
    if algo_key_marker and algo_key_marker not in ("unknown", ""):
        try:
            from app.core.code_marker import mark_code
            marker_result = mark_code(code, algo_key_marker, tree=code_tree)
        except Exception:
            pass

    # --- 4. 创建提交记录（flush 而非 commit，异常可整体回滚）---
    submission = Submission(
        user_id=session["user_id"],
        problem_id=problem_id,
        code=code,
        status="pending",
        recognized_algo=recognized,
    )
    db.session.add(submission)
    db.session.flush()

    # --- 4. 逐用例评测（包裹在 try 中，异常回滚）---
    test_cases = problem.test_cases.all()
    if not test_cases:
        db.session.rollback()
        return jsonify({"error": "本题无测试用例"}), 400

    passed_count = 0
    has_error = False
    has_timeout = False
    feedback_summary = None
    detail_ids = []  # 在循环中收集，避免最终 lazy query

    try:
        for tc in test_cases:
            # 解析输入
            try:
                input_arr = json.loads(tc.input_data)
            except (json.JSONDecodeError, ValueError):
                input_arr = []

            # 包装学生代码：自动添加 stdin 读取和 stdout 输出
            wrapped_code = (
                "import json, sys\n"
                + code + "\n"
                + "if __name__ == '__main__':\n"
                + "    data = json.loads(sys.stdin.read())\n"
                + "    result = sort(data)\n"
                + "    print(json.dumps(result))\n"
            )

            # 4a. 沙箱执行
            stdin_text = json.dumps(input_arr)
            run_result = run_code(wrapped_code, stdin_text)

            if run_result["timed_out"]:
                has_timeout = True
                detail = SubmissionDetail(
                    submission_id=submission.id,
                    test_case_id=tc.id,
                    input_arr=tc.input_data,
                    actual_output=None,
                    passed=False,
                    feedback="代码执行超时（超过 5 秒）——检查循环终止条件",
                )
                db.session.add(detail)
                continue

            if run_result["returncode"] != 0:
                has_error = True
                diag = diagnose(code, run_result, recognized)
                detail = SubmissionDetail(
                    submission_id=submission.id,
                    test_case_id=tc.id,
                    input_arr=tc.input_data,
                    actual_output=run_result.get("stdout", ""),
                    passed=False,
                    feedback=diag["hint"] if diag else run_result.get("stderr", ""),
                )
                db.session.add(detail)
                if feedback_summary is None and diag:
                    feedback_summary = diag
                continue

            # 4b. 比对输出
            actual_output = run_result["stdout"].strip()
            cmp_result = compare_outputs(
                actual_output,
                tc.expected_output,
                input_arr,
                problem.sort_rule,
            )

            detail = SubmissionDetail(
                submission_id=submission.id,
                test_case_id=tc.id,
                input_arr=tc.input_data,
                actual_output=actual_output,
                passed=cmp_result["passed"],
                feedback=cmp_result["reason"] if not cmp_result["passed"] else None,
            )
            db.session.add(detail)
            db.session.flush()
            detail_ids.append(detail.id)

            if cmp_result["passed"]:
                passed_count += 1
            elif feedback_summary is None:
                feedback_summary = {"type": "输出错误", "hint": cmp_result["reason"]}

            # 4c. 步骤采集（始终执行——可视化冗余设计）
            try:
                steps = collect_steps(code, input_arr,
                                         tree=code_tree,
                                         recognized_algo=recognized,
                                         marker_result=marker_result)
                if steps:
                    step_dicts = []
                    for step in steps:
                        step_dicts.append({
                            "detail_id": detail.id,
                            "seq": step["seq"],
                            "array_state": json.dumps(step["array_state"]),
                            "op": step["op"],
                            "i": step.get("i"),
                            "j": step.get("j"),
                            "note": step.get("note", ""),
                            "highlight_line": step.get("highlight_line"),
                            "round_num": step.get("round"),
                        })
                    db.session.bulk_insert_mappings(SortStep, step_dicts)
            except Exception as e:
                logger.warning(
                    "Step collection failed for submission %d, test_case %d: %s",
                    submission.id, tc.id, e
                )

        # --- 5. 汇总 ---
        total = len(test_cases)
        if has_error:
            submission.status = "error"
        elif has_timeout:
            submission.status = "timeout"
        elif passed_count == total:
            submission.status = "pass"
        else:
            submission.status = "fail"

        submission.score = int(passed_count / total * 100) if total > 0 else 0
        db.session.commit()

    except Exception:
        db.session.rollback()
        logger.exception("评测流程异常，已回滚")
        return jsonify({"error": "评测系统内部错误，请重试"}), 500

    # 6. 自动效率分析（全部用例通过时自动触发——在同一事务内）
    estimated_complexity = None
    if passed_count == total and total > 0 and problem.complexity_ceiling:
        try:
            from app.core.complexity import estimate as estimate_complexity
            result = estimate_complexity(code)
            estimated_complexity = result.get("estimated")
            from app.models import ComplexityAnalysis
            from app.core.algo_profiles import get_profile, check_ceiling as check_c
            profile = get_profile(recognized)
            theoretical = profile["average"] if profile else None
            ceiling_check = check_c(estimated_complexity, problem.complexity_ceiling)
            analysis = ComplexityAnalysis(
                submission_id=submission.id,
                estimated=estimated_complexity,
                theoretical=theoretical,
                timings=json.dumps(result.get("timings", {})),
                ratio=result.get("max_ratio"),
                meets_ceiling=ceiling_check["meets"],
            )
            db.session.add(analysis)
            # 不单独 commit，由下方统一提交
        except Exception as e:
            logger.warning("Auto complexity analysis failed: %s", e)

    # 评分
    grade_report = grade(
        code=code,
        passed_count=passed_count,
        total_cases=total,
        expected_algo=problem.algo_type,
        sort_rule=problem.sort_rule,
        complexity_ceiling=problem.complexity_ceiling,
        estimated_complexity=estimated_complexity,
        static_issues=static_issues,
        recognized=recognized,
    )
    return jsonify({
        "submission_id": submission.id,
        "detail_ids": detail_ids,
        "status": submission.status,
        "score": submission.score,
        "grade": grade_report,
        "recognized_algo": recognized,
        "passed": f"{passed_count}/{total}",
        "feedback": feedback_summary,
    })


@submit_bp.route("/history")
@login_required
def submission_history():
    """查看提交历史。"""
    submissions = (
        Submission.query
        .options(joinedload(Submission.problem))
        .filter_by(user_id=session["user_id"])
        .order_by(Submission.submitted_at.desc())
        .all()
    )
    return render_template("history.html", submissions=submissions)


@submit_bp.route("/result/<int:submission_id>")
@login_required
def submission_result(submission_id: int):
    """查看单次提交的评测结果。"""
    submission = Submission.query.options(
        joinedload(Submission.problem),
        joinedload(Submission.details).joinedload(SubmissionDetail.test_case)
    ).get_or_404(submission_id)
    details = submission.details
    return render_template("result.html", submission=submission, details=details)


# ---- 可视化 ----

@submit_bp.route("/visualize/<int:submission_id>")
@login_required
def visualize(submission_id: int):
    """排序过程可视化页面——学生实际代码 + 动画。"""
    submission = Submission.query.get_or_404(submission_id)
    details = submission.details.all()

    # 尝试获取代码行标记（用于前端语法高亮）
    code_lines = submission.code.split("\n")
    try:
        from app.core.recognizer import recognize_algorithm
        from app.core.code_marker import mark_code
        recognized = recognize_algorithm(submission.code)
        algo = recognized.split("(")[0].strip().split("/")[0].strip() if recognized else ""
        if algo:
            marker = mark_code(submission.code, algo)
            if marker and marker.get("code_lines"):
                code_lines = marker["code_lines"]
    except Exception:
        pass

    return render_template("visualize.html", submission=submission, details=details,
                           student_code=submission.code, code_lines=code_lines)


# ---- 可视化 API ----

@submit_bp.route("/api/steps/<int:detail_id>")
@login_required
def get_steps(detail_id: int):
    """获取某个测试用例的排序步骤（可视化数据源）。"""
    steps = (
        SortStep.query
        .filter_by(detail_id=detail_id)
        .order_by(SortStep.seq)
        .all()
    )
    return jsonify([{
        "seq": s.seq,
        "array_state": json.loads(s.array_state),
        "op": s.op,
        "i": s.i,
        "j": s.j,
        "note": s.note,
        "highlight_line": s.highlight_line,
        "round": s.round_num,
    } for s in steps])


# ---- 复杂度分析 API（按需触发，Phase 6 完善）----

@submit_bp.route("/api/complexity/<int:submission_id>", methods=["POST"])
@login_required
def analyze_complexity(submission_id: int):
    """触发复杂度分析（按需，多规模实测反推）。"""
    from app.core.complexity import estimate
    from app.core.algo_profiles import get_profile, check_ceiling
    from app.models import ComplexityAnalysis

    submission = Submission.query.get_or_404(submission_id)

    # 检查是否已分析过
    existing = ComplexityAnalysis.query.filter_by(submission_id=submission_id).first()
    if existing:
        return jsonify({
            "estimated": existing.estimated,
            "theoretical": existing.theoretical,
            "timings": json.loads(existing.timings) if existing.timings else {},
            "ratio": existing.ratio,
            "meets_ceiling": existing.meets_ceiling,
            "cached": True,
        })

    result = estimate(submission.code)

    # 获取理论复杂度
    profile = get_profile(submission.recognized_algo or "")
    theoretical = profile["average"] if profile else None

    # 与题目门槛对比
    ceiling_check = check_ceiling(
        result["estimated"],
        submission.problem.complexity_ceiling
    )

    # 持久化
    analysis = ComplexityAnalysis(
        submission_id=submission_id,
        estimated=result["estimated"],
        theoretical=theoretical,
        timings=json.dumps(result["timings"]),
        ratio=result.get("max_ratio"),
        meets_ceiling=ceiling_check["meets"],
    )
    db.session.add(analysis)
    db.session.commit()

    return jsonify({
        "estimated": result["estimated"],
        "theoretical": theoretical,
        "timings": result["timings"],
        "ratio": result.get("max_ratio"),
        "meets_ceiling": ceiling_check["meets"],
        "ceiling_message": ceiling_check["message"],
        "cached": False,
    })
