"""步骤采集器：拦截 list 操作，记录排序过程每一步的数组快照。

这是"可视化冗余设计"的核心——采集层与渲染层物理分离。
采集器产出统一的 {seq, array_state, op, i, j, note, highlight_line, round} 结构，
渲染层只认这个结构，任何一端缺失不影响另一端。

三种策略（按可靠性递减）：
- 策略 C: 标准算法重放（识别 + 模拟 + 行映射，推荐）
- 策略 A: TrackedList 拦截 __setitem__（零侵入，回退用）
- 策略 B: AST 插桩注入记录语句（预留）
"""
import ast
from typing import Any

from app.core.tracked_list import TrackedList


# ── 算法名规范化 ────────────────────────────────────────

def _normalize_algo(recognized: str) -> str:
    """从 recognizer 返回的字符串中提取简单算法键。

    "bubble(冒泡排序)" → "bubble"
    "select/insert(选择/插入)" → "select"  (fallback to first)
    """
    if not recognized:
        return ""
    key = recognized.split("(")[0].strip().split("/")[0].strip()
    return key


# ── 主入口 ──────────────────────────────────────────────

def collect_steps(code: str, input_arr: list, max_steps: int = 500,
                  strategy: str = "replay",
                  tree: "ast.AST | None" = None,
                  recognized_algo: str | None = None,
                  marker_result: dict | None = None) -> list[dict]:
    """采集排序过程的步骤快照。

    Args:
        code: 学生提交的 Python 代码。
        input_arr: 输入数组。
        max_steps: 最大采集步骤数（防止内存溢出）。
        strategy: 采集策略，默认 "replay"（标准算法重放）。
        tree: 预解析的 AST（可选，跳过重复解析）。
        recognized_algo: 预识别的算法（可选，跳过重复识别）。
        marker_result: 预计算的代码标记结果（可选，跳过重复标记）。

    Returns:
        list[dict]: 步骤列表。
    """
    if strategy == "replay":
        return _collect_replay(code, input_arr, max_steps,
                               tree=tree, recognized_algo=recognized_algo,
                               marker_result=marker_result)
    elif strategy == "tracked":
        return _collect_tracked(code, input_arr, max_steps)
    elif strategy == "ast_instrument":
        return _collect_ast_instrument(code, input_arr, max_steps)
    else:
        return [{"seq": 0, "array_state": list(input_arr), "op": "error",
                 "i": None, "j": None, "note": f"未知策略: {strategy}",
                 "highlight_line": None, "round": 0}]


# ── 策略 C：标准算法重放（推荐）───────────────────────

def _collect_replay(code: str, input_arr: list, max_steps: int,
                    tree=None, recognized_algo: str | None = None,
                    marker_result: dict | None = None) -> list[dict]:
    """策略 C：识别算法 → 标记代码行 → 模拟执行 → 附加行号。

    产出丰富步骤（含 compare/swap/set/init/done）和准确的代码行映射。
    失败时回退到策略 A（TrackedList）。
    
    Args:
        tree: 预解析的 AST（可选）。
        recognized_algo: 预识别的算法（可选，跳过 recognize_algorithm 调用）。
        marker_result: 预计算的代码标记（可选，跳过 mark_code 调用）。
    """
    try:
        from app.core.recognizer import recognize_algorithm
        from app.core.code_marker import mark_code
        from app.core.algo_simulators import simulate
    except ImportError:
        return _collect_tracked(code, input_arr, max_steps)

    # 1. 识别算法（优先使用传入结果）
    try:
        if recognized_algo is not None:
            recognized = recognized_algo
        else:
            recognized = recognize_algorithm(code, tree=tree)
    except Exception:
        return _collect_tracked(code, input_arr, max_steps)

    algo = _normalize_algo(recognized)
    if not algo or algo == "unknown":
        return _collect_tracked(code, input_arr, max_steps)

    # 2. 标记代码行（优先使用传入结果）
    line_map = None
    try:
        if marker_result is not None:
            line_map = marker_result.get("lines", {})
        else:
            mr = mark_code(code, algo, tree=tree)
            if mr:
                line_map = mr.get("lines", {})
    except Exception:
        pass  # 标记失败不致命，步骤不含行号即可

    # 3. 模拟执行
    try:
        steps = simulate(algo, list(input_arr))
    except Exception:
        return _collect_tracked(code, input_arr, max_steps)

    if not steps:
        return _collect_tracked(code, input_arr, max_steps)

    # 4. 附加行号和截断
    if line_map:
        for step in steps:
            op = step.get("op", "")
            if op == "init":
                step["highlight_line"] = (line_map.get("outer_loop")
                                          or line_map.get("compare")
                                          or line_map.get("return"))
            elif op == "compare":
                step["highlight_line"] = (line_map.get("compare")
                                          or line_map.get("inner_loop")
                                          or line_map.get("outer_loop"))
            elif op == "swap":
                step["highlight_line"] = (line_map.get("swap")
                                          or line_map.get("compare"))
            elif op == "set":
                step["highlight_line"] = (line_map.get("swap")
                                          or line_map.get("compare"))
            elif op == "done":
                step["highlight_line"] = (line_map.get("return")
                                          or line_map.get("outer_loop"))
            else:
                step["highlight_line"] = None
    else:
        for step in steps:
            step["highlight_line"] = None

    # 截断
    if len(steps) > max_steps:
        steps = steps[:max_steps]
        steps.append({
            "seq": len(steps),
            "array_state": steps[-1]["array_state"] if steps else list(input_arr),
            "op": "warning",
            "i": None, "j": None,
            "note": f"步骤已达上限 {max_steps}，后续步骤被截断",
            "highlight_line": None,
            "round": 0,
        })

    # 重新编号
    for idx, step in enumerate(steps):
        step["seq"] = idx

    return steps


# ── 策略 A：TrackedList 拦截（回退）────────────────────

def _collect_tracked(code: str, input_arr: list, max_steps: int) -> list[dict]:
    """策略 A：在受限命名空间中执行代码，用 TrackedList 拦截变更。

    零侵入，不修改学生代码。覆盖大部分原地排序（冒泡/选择/插入）。
    局限性：内置 list.sort() 和 sorted() 会绕过 __setitem__ 拦截。
    """
    steps: list[dict] = []
    tracked = TrackedList(input_arr, steps=steps, max_steps=max_steps)

    # 记录初始状态
    steps.append({
        "seq": 0, "array_state": list(tracked),
        "op": "init", "i": None, "j": None, "note": "初始数组",
        "highlight_line": None, "round": 0,
    })

    try:
        tree = ast.parse(code)
        compiled = compile(tree, "<student>", "exec")
        ns: dict[str, Any] = {"arr": tracked}
        exec(compiled, ns)

        if "sort" in ns and callable(ns["sort"]):
            result = ns["sort"](tracked)
            steps.append({
                "seq": len(steps),
                "array_state": (list(result)
                                if result is not None
                                else list(tracked)),
                "op": "done", "i": None, "j": None, "note": "排序完成",
                "highlight_line": None, "round": 0,
            })
        else:
            steps.append({
                "seq": len(steps), "array_state": list(tracked),
                "op": "done", "i": None, "j": None,
                "note": "无 sort() 函数，取 arr 最终状态",
                "highlight_line": None, "round": 0,
            })
    except SyntaxError as e:
        steps.append({
            "seq": len(steps), "array_state": list(tracked),
            "op": "error", "i": None, "j": None,
            "note": f"语法错误: {e.msg} (line {e.lineno})",
            "highlight_line": None, "round": 0,
        })
    except Exception as e:
        steps.append({
            "seq": len(steps), "array_state": list(tracked),
            "op": "error", "i": None, "j": None,
            "note": f"{type(e).__name__}: {e}",
            "highlight_line": None, "round": 0,
        })

    # 附加 default 值
    for s in steps:
        s.setdefault("highlight_line", None)
        s.setdefault("round", 0)

    return steps


# ── 策略 B：AST 插桩（预留）────────────────────────────

def _collect_ast_instrument(code: str, input_arr: list,
                            max_steps: int) -> list[dict]:
    """策略 B：分析 AST，在交换点注入记录语句（最精确）。

    当前为预留接口，返回提示。实际实现需改写 AST。
    """
    return [{
        "seq": 0, "array_state": list(input_arr),
        "op": "error", "i": None, "j": None,
        "note": "AST 插桩策略尚未实现（Phase 5 可选扩展）",
        "highlight_line": None, "round": 0,
    }]