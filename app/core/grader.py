"""代码评分引擎 — 10 分制，四维度打分 + 详细评语 + 示例代码。"""
from app.core.examples import EXAMPLE_CODE
from app.core.feedback import static_check_sort
from app.core.recognizer import recognize_algorithm
from app.core.algo_profiles import get_profile, check_ceiling


def _algo_key(recognized: str) -> str:
    """从识别结果提取纯 key。"""
    return recognized.split("(")[0].strip() if "(" in recognized else recognized


def grade(code: str, passed_count: int, total_cases: int,
          expected_algo: str = "any", sort_rule: str = "strict",
          complexity_ceiling: str | None = None,
          estimated_complexity: str | None = None,
          static_issues: list | None = None,
          recognized: str | None = None) -> dict:
    """10 分制评分。

    Returns:
        {
            "total": int,         总分 0-10
            "correctness": {score, max, detail}
            "algorithm":   {score, max, detail, detected, expected, example}
            "quality":     {score, max, detail, issues}
            "efficiency":  {score, max, detail, estimated, theoretical}
        }
    """
    recognized = recognized if recognized is not None else recognize_algorithm(code)
    if static_issues is None:
        static_issues = static_check_sort(code)

    # ── 1. 正确性 (0-4) ──
    if total_cases == 0:
        c_score, c_detail = 0, "无测试用例"
    else:
        ratio = passed_count / total_cases
        if ratio == 1.0:
            c_score, c_detail = 4, f"全部 {total_cases} 组测试用例通过 ✅"
        elif ratio >= 0.75:
            c_score, c_detail = 3, f"{passed_count}/{total_cases} 通过，大部分正确"
        elif ratio >= 0.5:
            c_score, c_detail = 2, f"{passed_count}/{total_cases} 通过，约半数正确"
        elif ratio > 0:
            c_score, c_detail = 1, f"仅 {passed_count}/{total_cases} 通过，逻辑有较大问题"
        else:
            c_score, c_detail = 0, f"0/{total_cases} 通过，全部用例失败"

    # ── 2. 算法匹配度 (0-2) ──
    algo_key = _algo_key(recognized)
    is_known = algo_key in ("bubble", "select", "insert", "quick", "merge", "heap")
    is_expected = expected_algo == "any" or algo_key == expected_algo

    if is_known and is_expected:
        a_score, a_detail = 2, f"✅ 算法识别: {recognized}，与题目要求一致"
    elif is_known and not is_expected:
        a_score, a_detail = 1, f"⚠️ 算法为 {recognized}，与题目要求的 {expected_algo} 不同"
    elif is_expected and not is_known:
        a_score, a_detail = 1, f"算法无法识别，但输出可能正确"
    else:
        a_score, a_detail = 0, f"❌ 算法无法识别 ({recognized})，与题目要求不符"

    # 示例代码
    target = expected_algo if expected_algo != "any" else algo_key
    example = EXAMPLE_CODE.get(target) or EXAMPLE_CODE.get("bubble", "")

    # ── 3. 代码质量 (0-2) ──
    danger_issues = [i for i in static_issues if i["type"] == "安全警告"]
    struct_issues = [i for i in static_issues if i["type"] != "安全警告"]

    # 语义校验错误数（severity="error" 的算错，warning 不算）
    semantic_errors = [i for i in static_issues if i.get("severity") == "error"
                       and i.get("type") not in ("安全警告", "语法错误")]
    semantic_warnings = [i for i in static_issues if i.get("severity") == "warning"
                         and i.get("type") not in ("安全警告", "语法错误")]

    if danger_issues:
        q_score = 0
        q_detail = f"含 {len(danger_issues)} 个安全风险: " + "; ".join(
            i["hint"][:60] for i in danger_issues[:3])
    elif struct_issues:
        q_score = 1
        q_detail = f"有 {len(struct_issues)} 个结构提醒: " + "; ".join(
            i["hint"][:60] for i in struct_issues[:3])
    elif semantic_errors:
        # 有语义逻辑错误 → 即使语法结构正常也扣分
        q_score = 1
        q_detail = f"代码语法结构正常，但检测到 {len(semantic_errors)} 个疑似算法逻辑缺陷: " + "; ".join(
            i["hint"][:80] for i in semantic_errors[:2])
    elif passed_count == 0 and total_cases > 0:
        # 无静态问题但全部用例失败 → 存在隐藏逻辑缺陷
        q_score = 1
        q_detail = f"代码语法结构正常但全部 {total_cases} 个测试用例均失败，算法逻辑可能存在严重缺陷"
    elif passed_count < total_cases and total_cases > 0:
        q_score = 2
        q_detail = f"代码结构良好，{passed_count}/{total_cases} 用例通过"
        if semantic_warnings:
            q_detail += "。" + "; ".join(i["hint"][:60] for i in semantic_warnings[:2])
    else:
        q_score = 2
        q_detail = "代码结构良好，未发现明显问题"

    # ── 4. 效率 (0-2) ──
    profile = get_profile(algo_key) if is_known else None
    theoretical = profile["average"] if profile else None

    if estimated_complexity and complexity_ceiling:
        ceiling_check = check_ceiling(estimated_complexity, complexity_ceiling)
        if ceiling_check["meets"]:
            e_score, e_detail = 2, f"实测 {estimated_complexity} ≤ 门槛 {complexity_ceiling} ✅"
        else:
            e_score, e_detail = 1, f"实测 {estimated_complexity} 超过门槛 {complexity_ceiling} ⚠️"
    elif estimated_complexity and theoretical:
        if estimated_complexity == theoretical:
            e_score, e_detail = 2, f"实测 {estimated_complexity}，与理论一致 ✅"
        else:
            e_score, e_detail = 1, f"实测 {estimated_complexity}，理论为 {theoretical}"
    elif c_score >= 4:
        e_score, e_detail = 1, "未分析复杂度（点击「分析复杂度」按钮可实测）"
    else:
        e_score, e_detail = 0, "未分析"

    total = c_score + a_score + q_score + e_score

    return {
        "total": total,
        "max": 10,
        "correctness": {"score": c_score, "max": 4, "detail": c_detail,
                        "passed": passed_count, "total_cases": total_cases},
        "algorithm": {"score": a_score, "max": 2, "detail": a_detail,
                      "detected": recognized, "expected": expected_algo,
                      "example": example},
        "quality": {"score": q_score, "max": 2, "detail": q_detail,
                    "issues": static_issues},
        "efficiency": {"score": e_score, "max": 2, "detail": e_detail,
                       "estimated": estimated_complexity,
                       "theoretical": theoretical},
    }
