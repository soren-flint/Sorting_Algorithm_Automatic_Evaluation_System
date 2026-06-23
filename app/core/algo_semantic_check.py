"""算法语义白盒校验模块。

在 recognizer 识别出算法类型后，对关键代码模式进行正确性校验。
检查比较方向、循环边界、递归终止条件、指针递增等语义细节。

设计原则：
- 不确定的判定降级为 warning，避免误杀非标准实现
- 可给出具体行号的精确定位
- 与 recognizer 共享 AST（避免重复解析）
"""

import ast
import re
from typing import Any

# ── 六种算法的语义校验规则 ──

def check_insertion_sort(tree: ast.AST, code_lines: list[str]) -> list[dict]:
    """插入排序语义校验：检查外循环起点、赋值位置、while 条件。"""
    issues = []

    for node in ast.walk(tree):
        # 找 "sort" 或顶层函数
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # 1. 外循环应从 range(1, n) 开始
        for outer_for in _find_for_loops(node):
            if not _is_range_call(outer_for.iter):
                continue
            range_args = outer_for.iter.args
            if len(range_args) == 1:
                # 单参数 range(n) 隐式从 0 开始
                issues.append({
                    "severity": "warning",
                    "line": outer_for.lineno,
                    "hint": "插入排序外循环通常从 range(1, n) 开始——单参数 range(n) 默认从 0 开始，i=0 时无左侧已排序区",
                })
            elif len(range_args) >= 2:
                arg0 = _get_constant(range_args[0])
                if arg0 == 0:
                    issues.append({
                        "severity": "warning",
                        "line": outer_for.lineno,
                        "hint": "插入排序外循环通常从 range(1, n) 开始——当前从 0 开始，i=0 时无左侧已排序区",
                    })

        # 2. 检查赋值位置 arr[j+1] = arr[j] 和 arr[j+1] = key
        for assign in _find_assigns(node):
            if not isinstance(assign, ast.Assign):
                continue
            for target in assign.targets:
                target_str = ast.unparse(target) if hasattr(ast, 'unparse') else _node_str(target)
                # 检查 arr[j] = arr[j-1] 模式（应为 arr[j+1] = arr[j]）
                if _is_subscript_offset(target, "j", 0) or _is_subscript_offset(target, "j", -1):
                    # 可能是 arr[j] = key（应为 arr[j+1] = key）
                    value_str = ast.unparse(assign.value) if hasattr(ast, 'unparse') else _node_str(assign.value)
                    if value_str in ("key", "arr[i]"):
                        issues.append({
                            "severity": "error",
                            "line": assign.lineno,
                            "hint": f"疑似赋值位置错误：第 {assign.lineno} 行应为 arr[j+1] = key，而不是 {_node_str(target)} = {value_str}。这会导致排序失效。",
                        })
                    elif value_str == "arr[j]":
                        issues.append({
                            "severity": "error",
                            "line": assign.lineno,
                            "hint": f"疑似赋值位置错误：第 {assign.lineno} 行可能是 arr[j+1] = arr[j]（右移一个位置）。检查下标是否正确。",
                        })

        # 3. while 条件检查
        for while_node in _find_while_loops(node):
            test_str = ast.unparse(while_node.test) if hasattr(ast, 'unparse') else _node_str(while_node.test)
            if "j >= 0" not in test_str and "j > -1" not in test_str:
                issues.append({
                    "severity": "warning",
                    "line": while_node.lineno,
                    "hint": f"插入排序 while 循环应包含边界检查 j >= 0 以保护数组头部。当前条件: {test_str}",
                })

    return issues


def check_merge_sort(tree: ast.AST, code_lines: list[str]) -> list[dict]:
    """归并排序语义校验：检查指针递增、剩余合并、递归终止。"""
    issues = []
    merge_func = None

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 找 merge 相关函数
            if "merge" in node.name.lower():
                merge_func = node
                break

    if merge_func is None:
        # 没有独立的 merge 函数，可能在 sort 内部内联
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if "sort" in node.name.lower() or node.name == "merge":
                    merge_func = node
                    break

    # 如果找到合并逻辑，检查关键步骤
    if merge_func:
        issues.extend(_check_merge_pointers(merge_func))
        issues.extend(_check_merge_remaining(merge_func))

    # 递归终止条件检查
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test_str = ast.unparse(node.test) if hasattr(ast, 'unparse') else _node_str(node.test)
            if "len(arr)" in test_str or "len(arr)" in test_str:
                if "== 1" in test_str and "<=" not in test_str and "< 2" not in test_str:
                    issues.append({
                        "severity": "error",
                        "line": node.lineno,
                        "hint": "递归终止条件不完整：应使用 len(arr) <= 1 处理空数组和单元素，当前仅处理 len(arr) == 1 会导致空数组下标越界",
                    })
                break  # 只需要检查第一个递归终止条件

    return issues


def _check_merge_pointers(func_node: ast.FunctionDef) -> list[dict]:
    """检查归并指针递增是否正确。"""
    issues = []
    # 找 i += 1 / j += 1 / k += 1 模式
    i_increments = []
    j_increments = []
    k_increments = []

    for node in ast.walk(func_node):
        if isinstance(node, ast.AugAssign):
            if isinstance(node.op, ast.Add):
                target_str = ast.unparse(node.target) if hasattr(ast, 'unparse') else _node_str(node.target)
                if target_str == "i":
                    i_increments.append(node.lineno)
                elif target_str == "j":
                    j_increments.append(node.lineno)
                elif target_str == "k":
                    k_increments.append(node.lineno)

    # 检查是否有完整的三个指针递增
    if not i_increments or not j_increments:
        issues.append({
            "severity": "error",
            "line": func_node.lineno,
            "hint": "归并排序缺少左/右子数组指针递增（i += 1 或 j += 1），可能导致部分元素遗漏",
        })

    return issues


def _check_merge_remaining(func_node: ast.FunctionDef) -> list[dict]:
    """检查是否有剩余元素合并步骤。"""
    issues = []
    # 找 while L 剩余 / while R 剩余的循环
    while_loops = list(_find_while_loops(func_node))
    # 找 extend 调用
    extend_calls = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "extend":
                    extend_calls.append(node.lineno)
            elif isinstance(node.func, ast.Name):
                if node.func.id == "extend":
                    extend_calls.append(node.lineno)

    if len(while_loops) < 2 and not extend_calls:
        issues.append({
            "severity": "error",
            "line": func_node.lineno,
            "hint": "归并排序可能需要合并剩余元素（while L[i:] / while R[j:] 或 extend），缺少此步骤会丢失未处理的数据",
        })

    return issues


def check_quick_sort(tree: ast.AST, code_lines: list[str]) -> list[dict]:
    """快速排序语义校验：检查分区比较方向、合并顺序。"""
    issues = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # 找列表推导式
        list_comps = []
        for child in ast.walk(node):
            if isinstance(child, ast.ListComp):
                list_comps.append(child)

        # 找 return 语句
        return_stmt = None
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                return_stmt = child
                break

        if len(list_comps) >= 2:
            # 检查分区比较方向（通过 Assign 节点关联变量名）
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name) and isinstance(child.value, ast.ListComp):
                            var_name = target.id  # "left" 或 "right" 或 "mid"
                            lc = child.value
                            if len(lc.generators) == 1:
                                gen = lc.generators[0]
                                if len(gen.ifs) == 1:
                                    if_test = gen.ifs[0]
                                    if isinstance(if_test, ast.Compare):
                                        # left 应该用 < pivot（取小的放左）
                                        if var_name == "left" and isinstance(if_test.ops[0], ast.Gt):
                                            issues.append({
                                                "severity": "error",
                                                "line": child.lineno,
                                                "hint": f"分区比较方向错误：第 {child.lineno} 行 left 使用 > pivot（取大的放左边），升序快排应为 < pivot",
                                            })
                                        # right 应该用 > pivot（取大的放右）
                                        if var_name == "right" and isinstance(if_test.ops[0], ast.Lt):
                                            issues.append({
                                                "severity": "error",
                                                "line": child.lineno,
                                                "hint": f"分区比较方向错误：第 {child.lineno} 行 right 使用 < pivot（取小的放右边），升序快排应为 > pivot",
                                            })

            # 找 pivot 赋值
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        target_str = ast.unparse(target) if hasattr(ast, 'unparse') else _node_str(target)
                        if target_str == "pivot":
                            # pivot 来源
                            if isinstance(child.value, ast.Subscript):
                                slice_val = child.value.slice
                                if isinstance(slice_val, ast.BinOp):
                                    if isinstance(slice_val.op, ast.FloorDiv):
                                        # arr[len(arr) // 2] - standard, ok
                                        pass

        # 检查 return 合并顺序
        if return_stmt and isinstance(return_stmt.value, ast.BinOp):
            if isinstance(return_stmt.value.op, ast.Add):
                # 递归调用 + mid + 递归调用 的模式
                return_str = ast.unparse(return_stmt.value) if hasattr(ast, 'unparse') else _node_str(return_stmt.value)
                # 检查是否 left 在前
                parts = return_str.split("+")
                parts = [p.strip() for p in parts]
                if len(parts) >= 3:
                    # 检查第一个递归调用的参数是否含 "right"
                    if "right" in parts[0].lower() and "left" in parts[-1].lower():
                        issues.append({
                            "severity": "error",
                            "line": return_stmt.lineno,
                            "hint": f"递归合并顺序错误：第 {return_stmt.lineno} 行先合并 right 再合并 left。升序快排应为 sort(left) + mid + sort(right)。两个错误可能恰好抵消，但算法实现不正确。",
                        })

    # 递归终止条件
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test_str = ast.unparse(node.test) if hasattr(ast, 'unparse') else _node_str(node.test)
            if "len(" in test_str:
                if "== 1" in test_str and "<=" not in test_str and "< 2" not in test_str:
                    issues.append({
                        "severity": "error",
                        "line": node.lineno,
                        "hint": "递归终止条件不完整：应使用 len(arr) <= 1 处理空数组和单元素。当前仅处理 len(arr) == 1，空数组会下标越界。",
                    })
                break

    return issues


def check_select_sort(tree: ast.AST, code_lines: list[str]) -> list[dict]:
    """选择排序语义校验：检查比较运算符方向、内循环范围。"""
    issues = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # 找内层循环中的比较
        for inner_for in _find_for_loops(node):
            # 跳过外循环本身 —— 外循环内可能有内循环
            for child in ast.walk(inner_for):
                if isinstance(child, ast.If):
                    if isinstance(child.test, ast.Compare):
                        if isinstance(child.test.ops[0], ast.Gt):
                            left_str = ast.unparse(child.test.left) if hasattr(ast, 'unparse') else _node_str(child.test.left)
                            right_str = ""
                            if len(child.test.comparators) == 1:
                                right_str = ast.unparse(child.test.comparators[0]) if hasattr(ast, 'unparse') else _node_str(child.test.comparators[0])
                            if "min" in right_str.lower() or "min" in left_str.lower():
                                issues.append({
                                    "severity": "error",
                                    "line": child.lineno,
                                    "hint": f"比较方向错误：第 {child.lineno} 行使用 > 查找最大值，升序选择排序应为 < 查找最小值。当前: {left_str} > {right_str}，应改为 {left_str} < {right_str}",
                                })
                        # 检查是否有比较符号写反但变量名含 max 的情况
                        if isinstance(child.test.ops[0], ast.Lt):
                            left_str = ast.unparse(child.test.left) if hasattr(ast, 'unparse') else _node_str(child.test.left)
                            if "max" in left_str.lower():
                                issues.append({
                                    "severity": "warning",
                                    "line": child.lineno,
                                    "hint": f"比较方向可疑：第 {child.lineno} 行变量含 'max' 但使用 < 比较。如果是查找最大值用于降序排序则没问题。",
                                })

        # 找 range(i+1, n-1) 边界遗漏
        for inner_for in _find_for_loops(node):
            if _is_range_call(inner_for.iter):
                range_args = inner_for.iter.args
                if len(range_args) >= 2:
                    arg1 = _get_constant(range_args[1])
                    # 第二个参数如果是 n-1（而非 n），最后一个元素被遗漏
                    if isinstance(range_args[1], ast.BinOp):
                        if isinstance(range_args[1].op, ast.Sub):
                            right_operand = _get_constant(range_args[1].right)
                            if right_operand == 1:
                                issues.append({
                                    "severity": "error",
                                    "line": inner_for.lineno,
                                    "hint": f"内层循环边界错误：第 {inner_for.lineno} 行上限为 n-1，数组最后一位元素永远无法进入比较。应改为 range(i+1, n)。",
                                })

    return issues


def check_bubble_sort(tree: ast.AST, code_lines: list[str]) -> list[dict]:
    """冒泡排序语义校验：检查比较方向、交换位置。"""
    issues = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for if_node in ast.walk(node):
            if isinstance(if_node, ast.If):
                if isinstance(if_node.test, ast.Compare):
                    if isinstance(if_node.test.ops[0], ast.Lt):
                        left_str = ast.unparse(if_node.test.left) if hasattr(ast, 'unparse') else _node_str(if_node.test.left)
                        right_str = ""
                        if len(if_node.test.comparators) == 1:
                            right_str = ast.unparse(if_node.test.comparators[0]) if hasattr(ast, 'unparse') else _node_str(if_node.test.comparators[0])
                        # 升序冒泡应为 arr[j] > arr[j+1]（大的往后冒）
                        if "arr[j]" in left_str and "arr[j+1]" in right_str:
                            issues.append({
                                "severity": "warning",
                                "line": if_node.lineno,
                                "hint": f"比较方向可能错误：第 {if_node.lineno} 行 {left_str} < {right_str} 是降序逻辑。升序冒泡应为 arr[j] > arr[j+1]（大的往后冒）。",
                            })

    return issues


def check_heap_sort(tree: ast.AST, code_lines: list[str]) -> list[dict]:
    """堆排序语义校验：检查 heapify 左右子节点下标。"""
    issues = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # 找 left = 2*i+1 或类似的子节点下标
        for assign in ast.walk(node):
            if isinstance(assign, ast.Assign):
                for target in assign.targets:
                    target_str = ast.unparse(target) if hasattr(ast, 'unparse') else _node_str(target)
                    if target_str in ("left", "l", "left_child"):
                        if isinstance(assign.value, ast.BinOp):
                            value_str = ast.unparse(assign.value) if hasattr(ast, 'unparse') else _node_str(assign.value)
                            if "2*i+1" not in value_str.replace(" ", "") and "2 * i + 1" not in value_str:
                                issues.append({
                                    "severity": "error",
                                    "line": assign.lineno,
                                    "hint": f"堆排序左子节点下标错误：第 {assign.lineno} 行应为 2*i+1。当前: {value_str}",
                                })

    return issues


# ── 公共入口 ──

def check_semantic(code: str, algo_type: str, tree: ast.AST | None = None) -> list[dict]:
    """对给定算法代码进行语义正确性校验。

    Args:
        code: 用户提交的 Python 代码
        algo_type: recognizer 识别出的算法类型（如 "quick"、"select"、"insert"、"merge"、"bubble"、"heap"）
        tree: 预解析的 AST（可选）。传入后跳过 ast.parse。

    Returns:
        list[dict]: 每项 {"severity": "error"|"warning", "line": int, "hint": str}
    """
    if tree is None:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []  # 语法错误由 feedback.py 处理

    code_lines = code.split("\n")

    # 按算法类型分发
    check_map = {
        "insert": check_insertion_sort,
        "select": check_select_sort,
        "quick": check_quick_sort,
        "merge": check_merge_sort,
        "bubble": check_bubble_sort,
        "heap": check_heap_sort,
    }

    # 兼容 recognizer 返回的带中文后缀格式，如 "quick (快速排序)"
    key = algo_type.split("(")[0].strip().lower() if "(" in algo_type else algo_type.strip().lower()

    checker = check_map.get(key)
    if checker is None:
        return []

    return checker(tree, code_lines)


# ── AST 辅助函数 ──

def _find_for_loops(node: ast.AST):
    """生成节点子树中所有 for 循环。"""
    for child in ast.walk(node):
        if isinstance(child, (ast.For, ast.AsyncFor)):
            yield child


def _find_while_loops(node: ast.AST):
    """生成节点子树中所有 while 循环。"""
    for child in ast.walk(node):
        if isinstance(child, ast.While):
            yield child


def _find_assigns(node: ast.AST):
    """生成节点子树中所有赋值语句。"""
    for child in ast.walk(node):
        if isinstance(child, ast.Assign):
            yield child


def _is_range_call(node: ast.AST) -> bool:
    """判断 AST 节点是否为 range(...) 调用。"""
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            return node.func.id == "range"
    return False


def _get_constant(node: ast.AST):
    """获取常量值。"""
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _is_subscript_offset(node: ast.AST, var: str, offset: int) -> bool:
    """判断节点是否为 arr[var+offset] 或 arr[var-offset] 模式。"""
    if not isinstance(node, ast.Subscript):
        return False
    # 检查下标是否为 Name(var) + offset
    slice_val = node.slice
    if isinstance(slice_val, ast.BinOp) and offset != 0:
        if isinstance(slice_val.op, ast.Add):
            if isinstance(slice_val.left, ast.Name) and slice_val.left.id == var:
                if _get_constant(slice_val.right) == offset:
                    return True
        elif isinstance(slice_val.op, ast.Sub):
            if isinstance(slice_val.left, ast.Name) and slice_val.left.id == var:
                if _get_constant(slice_val.right) == abs(offset):
                    return True if offset < 0 else False
    elif isinstance(slice_val, ast.Name) and offset == 0:
        return slice_val.id == var
    return False


def _node_str(node: ast.AST) -> str:
    """将 AST 节点转回字符串（兼容 Python 3.8）。"""
    if hasattr(ast, 'unparse'):
        return ast.unparse(node)
    # 回退方案：简单字符串表示
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Subscript):
        return f"{_node_str(node.value)}[{_node_str(node.slice)}]"
    return "<expr>"