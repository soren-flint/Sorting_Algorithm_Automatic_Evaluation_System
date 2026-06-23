"""输出比对器：比较学生输出与期望输出。

支持严格匹配和按规则推导两种模式：
- 有 expected_output 时直接比对 JSON 数组
- 无 expected_output 时交由 validator 按排序规则判定
"""
import json


def compare_outputs(actual_output: str, expected_output: str | None,
                    input_arr: list, sort_rule: str = "strict") -> dict:
    """比对实际输出与期望输出。

    Args:
        actual_output: 学生代码的实际 stdout 输出。
        expected_output: 期望输出（JSON 字符串），可为 None（由规则推导）。
        input_arr: 输入数组。
        sort_rule: 排序规则。

    Returns:
        dict: {
            "passed": bool,
            "actual_parsed": list | None,
            "expected_parsed": list | None,
            "reason": str,
            "diff": str | None,   # 差异描述
        }
    """
    # sort_rule 校验
    VALID_RULES = {"strict", "stalin", "stable", "topk"}
    if sort_rule not in VALID_RULES:
        return {
            "passed": False,
            "actual_parsed": None,
            "expected_parsed": None,
            "reason": f"未知的排序规则: {sort_rule}",
            "diff": None,
        }

    # 输入校验
    if not isinstance(actual_output, str):
        return {
            "passed": False,
            "actual_parsed": None,
            "expected_parsed": None,
            "reason": "实际输出不是字符串类型",
            "diff": None,
        }
    # 防止超大输出导致解析性能问题
    if len(actual_output) > 100_000:
        return {
            "passed": False,
            "actual_parsed": None,
            "expected_parsed": None,
            "reason": "输出过长（超过 100KB），可能为非预期输出",
            "diff": f"输出长度: {len(actual_output)}",
        }

    # 解析实际输出
    try:
        actual_parsed = json.loads(actual_output.strip())
    except (json.JSONDecodeError, ValueError):
        return {
            "passed": False,
            "actual_parsed": None,
            "expected_parsed": None,
            "reason": "无法解析实际输出为 JSON 数组",
            "diff": f"原始输出: {actual_output[:100]}",
        }

    if not isinstance(actual_parsed, list):
        return {
            "passed": False,
            "actual_parsed": actual_parsed,
            "expected_parsed": None,
            "reason": "实际输出不是 JSON 数组",
            "diff": f"输出类型: {type(actual_parsed).__name__}",
        }

    # 有期望输出 → 逐元素比对
    if expected_output is not None:
        try:
            expected_parsed = json.loads(expected_output)
        except (json.JSONDecodeError, ValueError):
            return {
                "passed": False,
                "actual_parsed": actual_parsed,
                "expected_parsed": None,
                "reason": "期望输出无法解析",
                "diff": None,
            }

        if actual_parsed == expected_parsed:
            return {
                "passed": True,
                "actual_parsed": actual_parsed,
                "expected_parsed": expected_parsed,
                "reason": "输出与期望完全一致",
                "diff": None,
            }
        else:
            diff_desc = _describe_diff(actual_parsed, expected_parsed)
            return {
                "passed": False,
                "actual_parsed": actual_parsed,
                "expected_parsed": expected_parsed,
                "reason": "输出与期望不一致",
                "diff": diff_desc,
            }

    # 无期望输出 → 由 validator 按规则判定
    from app.core.validator import validate_sort
    result = validate_sort(actual_parsed, input_arr, sort_rule)
    return {
        "passed": result["passed"],
        "actual_parsed": actual_parsed,
        "expected_parsed": None,
        "reason": result["reason"],
        "diff": None,
    }


def _describe_diff(actual: list, expected: list) -> str:
    """生成差异的智能可读描述，提供根因推断。

    对输出做多层分析：逆序检测、截断检测、局部乱序检测，
    给出代码级根因推断提示，帮助使用者快速定位缺陷。

    Args:
        actual: 实际输出。
        expected: 期望输出。

    Returns:
        str: 差异描述（含根因推断）。
    """
    parts: list[str] = []

    # ── 第1层：长度差异 ──
    if len(actual) != len(expected):
        parts.append(f"长度不同：实际 {len(actual)} 个元素，期望 {len(expected)} 个元素")
        if len(actual) < len(expected):
            # 可能循环边界过小、遗漏合并步骤、斯大林排序误杀
            diff_count = len(expected) - len(actual)
            parts.append(f"实际输出缺少 {diff_count} 个元素 —— 检查循环边界是否过小（如 range(i+1, n-1) 遗漏末尾）或归并时是否遗漏剩余元素合并")
        else:
            diff_count = len(actual) - len(expected)
            parts.append(f"实际输出多出 {diff_count} 个元素 —— 检查是否存在重复添加或循环边界过大")
        return " | ".join(parts)

    if not actual or not expected:
        return "输出为空"

    # ── 第2层：逆序检测 ──
    reversed_expected = list(reversed(expected))
    if actual == reversed_expected:
        parts.append("输出为期望的完全逆序（降序而非升序）")
        parts.append("根因推断：比较方向可能写反了（> 写成 < 或反之）；"
                     "快排场景还需检查分区条件 + 递归合并顺序是否同时倒置")
        return " | ".join(parts)

    # ── 第3层：缺失首/尾元素（边界截断） ──
    if expected[0] not in actual:
        parts.append(f"输出缺少最小元素 {expected[0]} —— 检查循环起始值是否跳过第一位")
    if expected[-1] not in actual:
        parts.append(f"输出缺少最大元素 {expected[-1]} —— 检查循环终止条件是否截断末尾")

    # ── 第4层：首/尾位置异常 ──
    if len(actual) >= 2 and len(expected) >= 2:
        if actual[0] != expected[0]:
            parts.append(f"首位错误：实际 {actual[0]}，期望 {expected[0]} —— 最小值查找可能有误")
        if actual[-1] != expected[-1]:
            parts.append(f"末位错误：实际 {actual[-1]}，期望 {expected[-1]} —— 最大值归位可能有误")

    # ── 第5层：局部已排序但部分错位 ──
    sorted_actual = sorted(actual)
    if sorted_actual == expected:
        parts.append("元素集合正确、仅顺序错误 —— 算法框架对但排序逻辑有缺陷")
        # 找出有多少位置不对
        mismatch_count = sum(1 for i in range(len(actual)) if actual[i] != expected[i])
        parts.append(f"{mismatch_count}/{len(expected)} 个位置错误")
    else:
        # 检查是否部分有序
        ascending_runs = _count_ascending_runs(actual)
        if ascending_runs <= 3:
            parts.append(f"输出仅 {ascending_runs} 段递增，排序不完整 —— 可能内循环未正确覆盖全部元素")
        else:
            # 找第一处不同
            for i, (a, e) in enumerate(zip(actual, expected)):
                if a != e:
                    parts.append(f"首个差异位 [{i}]：实际 {a}，期望 {e}")
                    break

    if not parts:
        parts.append("内容不同但长度相同 —— 建议逐元素对比查找根因")

    return " | ".join(parts)


def _count_ascending_runs(arr: list) -> int:
    """统计递增段数（用于判断排序完成度）。"""
    if len(arr) <= 1:
        return 1
    runs = 1
    for i in range(1, len(arr)):
        if arr[i] < arr[i - 1]:
            runs += 1
    return runs