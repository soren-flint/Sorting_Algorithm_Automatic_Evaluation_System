"""AST 代码行标记器：分析用户排序代码，找到关键行号映射。

用于可视化时高亮当前执行行。按算法类型调度不同的 AST 遍历策略。
"""
import ast
from typing import Optional


def mark_code(code: str, algo: str, tree: ast.AST | None = None) -> Optional[dict]:
    """分析用户代码，返回关键行号映射和代码行列表。

    Args:
        code: 用户提交的 Python 代码。
        algo: 识别出的算法类型（bubble|select|insert|quick|merge|heap）。

    Returns:
        None 如果分析失败；否则:
        {
            "algo": "bubble",
            "lines": {
                "outer_loop": 3,
                "inner_loop": 4,
                "compare": 5,
                "swap": 6,
                "return": 8,
            },
            "code_lines": ["def sort(arr):", "    n = len(arr)", ...]
        }
    """
    try:
        if tree is None:
            tree = ast.parse(code)
    except SyntaxError:
        return None

    # 按行拆分（去除末尾空行）
    raw_lines = code.split("\n")
    # 去除末尾连续空行
    while raw_lines and raw_lines[-1] == "":
        raw_lines.pop()

    # 根据算法类型调度标记函数
    markers = {
        "bubble": _mark_bubble,
        "select": _mark_select,
        "insert": _mark_insert,
        "quick": _mark_quick,
        "merge": _mark_merge,
        "heap": _mark_heap,
    }

    marker_fn = markers.get(algo)
    if marker_fn is None:
        return None

    lines = marker_fn(tree)
    if lines is None:
        # 尝试通用回退
        func = _find_sort_function(tree)
        if func is not None:
            lines = _generic_fallback(func)
        else:
            return None

    return {
        "algo": algo,
        "lines": lines,
        "code_lines": raw_lines,
    }


# ── 辅助函数 ────────────────────────────────────────────


def _find_sort_function(tree: ast.Module) -> Optional[ast.FunctionDef]:
    """查找名为 sort 的函数定义。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "sort":
            return node
    return None


def _is_adjacent_compare(test: ast.expr) -> bool:
    """检测是否是 arr[j] > arr[j+1] 或 arr[j] < arr[j+1] 形式的相邻比较。"""
    if not isinstance(test, ast.Compare):
        return False
    if len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    op = test.ops[0]
    if not isinstance(op, (ast.Gt, ast.Lt, ast.GtE, ast.LtE)):
        return False
    left = test.left
    right = test.comparators[0]
    # 检测 arr[x] ? arr[x+1] 模式
    if isinstance(left, ast.Subscript) and isinstance(right, ast.Subscript):
        # 粗略判断：右边索引是左边索引+1
        if isinstance(left.slice, ast.Constant) and isinstance(right.slice, ast.BinOp):
            return True
        if isinstance(left.slice, ast.BinOp) and isinstance(right.slice, ast.Constant):
            return True
        # 简单情况：两个都是 Constant（如 arr[0] > arr[1]）
        if isinstance(left.slice, ast.Constant) and isinstance(right.slice, ast.Constant):
            lv = left.slice.value
            rv = right.slice.value
            if isinstance(lv, int) and isinstance(rv, int) and rv == lv + 1:
                return True
    return False


def _is_swap(node: ast.Assign) -> bool:
    """检测是否是 a[i], a[j] = a[j], a[i] 形式的 swap。"""
    if len(node.targets) != 1:
        return False
    target = node.targets[0]
    value = node.value
    # 目标必须是元组
    if not isinstance(target, ast.Tuple):
        return False
    if not isinstance(value, ast.Tuple):
        return False
    # 两元素互换
    if len(target.elts) != 2 or len(value.elts) != 2:
        return False
    return True


def _find_return_line(body: list[ast.stmt]) -> Optional[int]:
    """在语句列表中查找 return 行号。"""
    for stmt in body:
        if isinstance(stmt, ast.Return):
            return stmt.lineno
    return None


# ── 通用回退 ────────────────────────────────────────────

def _generic_fallback(func: ast.FunctionDef) -> dict:
    """当算法特定标记失败时，提供基于函数结构的通用行号映射。"""
    body = func.body
    result: dict = {}

    # 第一个有意义的语句作为 outer_loop
    for stmt in body:
        if isinstance(stmt, (ast.For, ast.While, ast.If)):
            result["outer_loop"] = stmt.lineno
            break
    if "outer_loop" not in result and body:
        result["outer_loop"] = body[0].lineno
    if "outer_loop" not in result:
        result["outer_loop"] = 1

    # 找 return
    result["return"] = _find_return_line(body) or (result["outer_loop"] + 5)

    # 找比较（If 语句）
    for node in ast.walk(func):
        if isinstance(node, ast.If) and "compare" not in result:
            result["compare"] = node.lineno
            break
    result.setdefault("compare", result["outer_loop"] + 1)

    # 找交换/赋值
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and "swap" not in result:
            result["swap"] = node.lineno
            break
    result.setdefault("swap", result["compare"] + 1)

    # inner_loop
    result["inner_loop"] = result.get("outer_loop")

    return result


# ── 算法特定标记 ────────────────────────────────────────


def _mark_bubble(tree: ast.Module) -> Optional[dict]:
    """冒泡排序：嵌套 for + 相邻比较 + swap。"""
    func = _find_sort_function(tree)
    if func is None:
        return None

    result: dict = {}
    body = func.body

    for stmt in body:
        if isinstance(stmt, ast.For):
            # 外循环
            if "outer_loop" not in result:
                result["outer_loop"] = stmt.lineno
                # 找内循环
                for inner in stmt.body:
                    if isinstance(inner, ast.For):
                        result["inner_loop"] = inner.lineno
                        # 找比较和交换
                        for innermost in inner.body:
                            if isinstance(innermost, ast.If):
                                result.setdefault("compare", innermost.lineno)
                                for swap_stmt in innermost.body:
                                    if isinstance(swap_stmt, ast.Assign) and _is_swap(swap_stmt):
                                        result["swap"] = swap_stmt.lineno
                                        break
                            elif isinstance(innermost, ast.Assign) and "swap" not in result:
                                result["swap"] = innermost.lineno
        elif isinstance(stmt, ast.Return) and "return" not in result:
            result["return"] = stmt.lineno

    if "outer_loop" not in result:
        return None
    result.setdefault("return", _find_return_line(body) or (result["outer_loop"] + 5))
    result.setdefault("inner_loop", result["outer_loop"] + 1)
    result.setdefault("compare", result.get("inner_loop", result["outer_loop"]) + 1)
    result.setdefault("swap", result["compare"] + 1)
    return result


def _mark_select(tree: ast.Module) -> Optional[dict]:
    """选择排序：外层 for + min_idx 追踪 + 内层 for + 末尾 swap。"""
    func = _find_sort_function(tree)
    if func is None:
        return None

    result: dict = {}
    body = func.body

    for stmt in body:
        if isinstance(stmt, ast.For):
            if "outer_loop" not in result:
                result["outer_loop"] = stmt.lineno
                # 在内层找 for（选择排序的第二个 for）
                after_min = False
                for inner in stmt.body:
                    if isinstance(inner, ast.Assign):
                        # min_idx = i
                        after_min = True
                    elif isinstance(inner, ast.For):
                        result["inner_loop"] = inner.lineno
                        for innermost in inner.body:
                            if isinstance(innermost, ast.If):
                                result.setdefault("compare", innermost.lineno)
                                # 里面的赋值是 min_idx = j，不是 swap
                            elif isinstance(innermost, ast.Assign) and "compare" not in result:
                                result.setdefault("compare", innermost.lineno)
                    elif isinstance(inner, ast.If):
                        result.setdefault("swap", inner.lineno)
                        for swap_stmt in inner.body:
                            if isinstance(swap_stmt, ast.Assign):
                                result["swap"] = swap_stmt.lineno
        elif isinstance(stmt, ast.Return) and "return" not in result:
            result["return"] = stmt.lineno

    if "outer_loop" not in result:
        return None
    result.setdefault("return", _find_return_line(body) or (result["outer_loop"] + 5))
    result.setdefault("inner_loop", result["outer_loop"] + 1)
    result.setdefault("compare", result.get("inner_loop", result["outer_loop"]) + 1)
    result.setdefault("swap", result["compare"] + 1)
    return result


def _mark_insert(tree: ast.Module) -> Optional[dict]:
    """插入排序：外层 for + key 赋值 + while 内移 + 末尾 key 归位。"""
    func = _find_sort_function(tree)
    if func is None:
        return None

    result: dict = {}
    body = func.body

    for stmt in body:
        if isinstance(stmt, ast.For):
            if "outer_loop" not in result:
                result["outer_loop"] = stmt.lineno
                for inner in stmt.body:
                    if isinstance(inner, ast.While):
                        result["inner_loop"] = inner.lineno
                        # while 条件就是比较
                        result.setdefault("compare", inner.lineno)
                        for while_stmt in inner.body:
                            if isinstance(while_stmt, ast.Assign):
                                result.setdefault("swap", while_stmt.lineno)
                                break
                            elif isinstance(while_stmt, ast.AugAssign):
                                result.setdefault("swap", while_stmt.lineno)
                    elif isinstance(inner, ast.Assign) and "swap" not in result:
                        # arr[j+1] = key (最后的赋值)
                        result.setdefault("swap", inner.lineno)
        elif isinstance(stmt, ast.Return) and "return" not in result:
            result["return"] = stmt.lineno

    if "outer_loop" not in result:
        return None
    result.setdefault("return", _find_return_line(body) or (result["outer_loop"] + 5))
    result.setdefault("inner_loop", result["outer_loop"] + 1)
    result.setdefault("compare", result.get("inner_loop", result["outer_loop"]))
    result.setdefault("swap", result["compare"] + 1)
    return result


def _mark_quick(tree: ast.Module) -> Optional[dict]:
    """快速排序：递归 + partition（内层 for + if + swap + pivot 归位）。"""
    func = _find_sort_function(tree)
    if func is None:
        return None

    result: dict = {}
    body = func.body

    # 快排可能直接在 sort 里递归，也可能调用 partition
    # 先找递归调用和比较/交换
    for node in ast.walk(func):
        if isinstance(node, ast.For) and "outer_loop" not in result:
            # partition 内的 for 循环
            result["outer_loop"] = node.lineno
            for inner in node.body:
                if isinstance(inner, ast.If):
                    result.setdefault("compare", inner.lineno)
                    for if_stmt in inner.body:
                        if isinstance(if_stmt, ast.If):
                            # 嵌套 if（i != j 检查）
                            for nested in if_stmt.body:
                                if isinstance(nested, ast.Assign):
                                    result.setdefault("swap", nested.lineno)
                        elif isinstance(if_stmt, ast.Assign):
                            # swap
                            result.setdefault("swap", if_stmt.lineno)
        elif isinstance(node, ast.If) and "compare" not in result:
            # 可能是 len(arr) <= 1 检查
            pass
        elif isinstance(node, ast.Return):
            result.setdefault("return", node.lineno)
        elif isinstance(node, ast.Assign) and "swap" not in result:
            # pivot 归位 swap
            if isinstance(node.value, ast.Tuple):
                result.setdefault("swap", node.lineno)

    if "outer_loop" not in result:
        # Fallback 1: Look for any for loop
        for node in ast.walk(func):
            if isinstance(node, ast.For):
                result["outer_loop"] = node.lineno
                break

    if "outer_loop" not in result:
        # Fallback 2: Functional-style quick sort (list comprehensions, no for loops)
        # Use the first if-statement (base case) or first statement as outer_loop
        for stmt in body:
            if isinstance(stmt, ast.If):
                result["outer_loop"] = stmt.lineno
                result.setdefault("compare", stmt.lineno)
                break
        if "outer_loop" not in result and body:
            result["outer_loop"] = body[0].lineno

    if "outer_loop" not in result:
        return None
    result.setdefault("return", _find_return_line(body) or (result["outer_loop"] + 6))
    result.setdefault("compare", result.get("compare") or result["outer_loop"] + 1)
    result.setdefault("swap", result["compare"] + 1)
    result.setdefault("inner_loop", result.get("outer_loop"))
    return result


def _mark_merge(tree: ast.Module) -> Optional[dict]:
    """归并排序：递归 + merge 函数（while 双指针 + 比较 + 赋值）。"""
    func = _find_sort_function(tree)
    if func is None:
        return None

    result: dict = {}
    body = func.body

    # 找 merge 相关的 while 循环（双指针比较）
    for node in ast.walk(func):
        if isinstance(node, ast.While) and "outer_loop" not in result:
            # 双指针 while left and right
            result["outer_loop"] = node.lineno
            for inner in node.body:
                if isinstance(inner, ast.If):
                    result.setdefault("compare", inner.lineno)
                    for if_stmt in inner.body:
                        if isinstance(if_stmt, ast.Assign):
                            result.setdefault("swap", if_stmt.lineno)
                        elif isinstance(if_stmt, ast.Expr) and isinstance(if_stmt.value, ast.Call):
                            result.setdefault("swap", if_stmt.lineno)
                elif isinstance(inner, ast.Assign):
                    result.setdefault("swap", inner.lineno)
        elif isinstance(node, ast.Return):
            result.setdefault("return", node.lineno)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and "swap" not in result:
            # .append call
            result.setdefault("swap", node.lineno)

    if "outer_loop" not in result:
        # Fallback: look for any while loop
        for node in ast.walk(func):
            if isinstance(node, ast.While):
                result["outer_loop"] = node.lineno
                break

    if "outer_loop" not in result:
        return None
    result.setdefault("return", _find_return_line(body) or (result["outer_loop"] + 5))
    result.setdefault("compare", result["outer_loop"] + 1)
    result.setdefault("swap", result["compare"] + 1)
    result.setdefault("inner_loop", result.get("outer_loop"))
    return result


def _mark_heap(tree: ast.Module) -> Optional[dict]:
    """堆排序：heapify 递归 + 建堆循环 + 排序循环 + swap。"""
    func = _find_sort_function(tree)
    if func is None:
        return None

    result: dict = {}
    body = func.body

    # 堆排序通常有 heapify 辅助函数和两个 for 循环
    for_loops = []
    for node in ast.walk(func):
        if isinstance(node, ast.For):
            for_loops.append(node)
        elif isinstance(node, ast.If) and "compare" not in result:
            # heapify 内的比较
            test = node.test
            if isinstance(test, ast.Compare) and isinstance(test.ops[0], ast.Gt):
                result["compare"] = node.lineno
                for inner in node.body:
                    if isinstance(inner, ast.Assign):
                        result.setdefault("swap", inner.lineno)
        elif isinstance(node, ast.Return):
            result.setdefault("return", node.lineno)
        elif isinstance(node, ast.Assign) and "swap" not in result:
            # swap(arr[0], arr[i])
            if isinstance(node.value, ast.Tuple):
                result.setdefault("swap", node.lineno)

    # 外循环 = 建堆循环（第一个 for）
    if for_loops:
        result.setdefault("outer_loop", for_loops[0].lineno)
        if len(for_loops) > 1:
            result["inner_loop"] = for_loops[1].lineno  # 排序循环

    if "outer_loop" not in result:
        return None
    result.setdefault("return", _find_return_line(body) or (result["outer_loop"] + 7))
    result.setdefault("compare", result["outer_loop"] + 1)
    result.setdefault("swap", result["compare"] + 1)
    result.setdefault("inner_loop", result.get("outer_loop", 0) + 3)
    return result