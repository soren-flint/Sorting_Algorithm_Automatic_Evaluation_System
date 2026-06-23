"""算法识别器：通过 AST 结构特征识别排序算法类型。

支持的识别：
- bubble  (冒泡): 双层循环 + 相邻交换 (a[j],a[j+1]=a[j+1],a[j])
- select  (选择): 双层循环 + 找最小值 + 单次交换
- insert  (插入): 双层循环 + while 内层 + 向后移动元素
- quick   (快排): 递归 + 分区逻辑
- merge   (归并): 递归 + 双指针合并
- heap    (堆排): 2i+1 下标 + 下沉操作

诚实声明：选择 vs 插入结构太像，识别不准时报 "select/insert"。
"""
import ast


def recognize_algorithm(code: str, tree: ast.AST | None = None) -> str:
    """通过 AST 结构特征识别排序算法类型。

    Args:
        code: 学生提交的 Python 源代码。
        tree: 预解析的 AST（可选）。传入后跳过 ast.parse，避免重复解析。

    Returns:
        str: 算法类型标识，如 "bubble(冒泡排序)"、"unknown(未识别)"。
    """
    if tree is None:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return "unknown(语法错误)"

    # 收集结构特征
    loops = [n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))]
    nested = _has_nested_loop(tree)
    has_swap = _has_adjacent_swap(tree)
    has_recursion = _has_recursion(tree)
    has_merge_pattern = _has_merge(tree)
    has_heap_pattern = _has_heap(tree)
    has_min_find = _has_min_find(tree)
    has_while_inner = _has_while_inner(tree)
    has_stalin_pattern = _has_stalin(tree)

    # 决策树
    if has_stalin_pattern:
        return "stalin(斯大林排序)"
    if has_recursion and has_merge_pattern:
        # 区分标准归并 vs 仁慈斯大林（有 kept/dropped 特征）
        if _has_merciful_stalin(tree):
            return "merciful_stalin(仁慈斯大林排序)"
        return "merge(归并排序)"
    if has_heap_pattern:
        return "heap(堆排序)"
    if has_recursion:
        return "quick(快速排序)"
    if nested and has_min_find and not has_while_inner:
        return "select(选择排序)"
    if nested and has_while_inner and not has_min_find:
        return "insert(插入排序)"
    if nested and has_min_find and has_while_inner:
        return "select/insert(选择/插入——结构相似，无法区分)"
    if nested and has_swap:
        return "bubble(冒泡排序)"
    if nested:
        return "select/insert(选择/插入)"
    if loops:
        return "iterative(普通迭代排序)"
    return "unknown(未识别)"


# ---- 辅助识别函数 ----

def _has_merciful_stalin(tree: ast.AST) -> bool:
    """检测仁慈斯大林排序特征：
    - 有递归调用
    - 有 kept 和 dropped 两个列表
    - 同时具有斯大林扫描模式（单层循环 + result[-1] 比较 + append）
    """
    has_kept = False
    has_dropped = False
    has_recursion = False
    has_last_access = False
    has_append = False
    has_single_loop = False

    for node in ast.walk(tree):
        # 检测 kept / dropped 变量
        if isinstance(node, ast.Name):
            if node.id == 'kept':
                has_kept = True
            if node.id == 'dropped':
                has_dropped = True
        # 检测 result[-1] 下标访问
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.UnaryOp) and isinstance(node.slice.op, ast.USub):
                if isinstance(node.slice.operand, ast.Constant) and node.slice.operand.value == 1:
                    has_last_access = True
        # 检测 .append() 调用
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "append":
                has_append = True
        # 检测单层 for 循环
        if isinstance(node, ast.For):
            has_single_loop = True

    has_recursion = _has_recursion(tree)
    return has_kept and has_dropped and has_recursion and has_last_access and has_append and has_single_loop


def _has_nested_loop(tree: ast.AST) -> bool:
    """检测是否存在嵌套循环。"""
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            for child in ast.walk(node):
                if child is not node and isinstance(child, (ast.For, ast.While)):
                    return True
    return False


def _has_adjacent_swap(tree: ast.AST) -> bool:
    """检测是否存在相邻元素交换 a[i],a[i+1]=a[i+1],a[i]。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            # 元组赋值：a, b = b, a
            if (len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Tuple)
                    and isinstance(node.value, ast.Tuple)):
                return True
    return False


def _has_recursion(tree: ast.AST) -> bool:
    """检测是否存在递归调用（函数体内调用自身）。"""
    func_names = {
        n.name for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in func_names:
                return True
    return False


def _has_merge(tree: ast.AST) -> bool:
    """检测归并特征：存在双指针（i,j独立递增）的合并逻辑。"""
    # 归并排序特征：函数内有 while i<len and j<len 的双指针合并
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            while_loops = [n for n in ast.walk(node)
                           if isinstance(n, ast.While)]
            for w in while_loops:
                # 检查 while 条件中是否含 and + 两个比较
                if isinstance(w.test, ast.BoolOp) and isinstance(w.test.op, ast.And):
                    if len(w.test.values) >= 2:
                        return True
    return False


def _has_heap(tree: ast.AST) -> bool:
    """检测堆排序特征：存在 2*i+1 或 2*i+2 这类下标计算。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp):
            # 检查是否有 2 * i + 1 模式
            if isinstance(node.op, ast.Add):
                left = node.left
                if isinstance(left, ast.BinOp) and isinstance(left.op, ast.Mult):
                    mult_left = left.left
                    if isinstance(mult_left, ast.Constant) and mult_left.value == 2:
                        right = node.right
                        if isinstance(right, ast.Constant) and right.value in (1, 2):
                            return True
    return False


def _has_min_find(tree: ast.AST) -> bool:
    """检测选择排序特征：内层循环中找最小值并记录下标。"""
    # 简化：检测是否有 min_val / min_idx 这类变量赋值
    min_vars = {"min_idx", "min_index", "min_val", "min_value", "min_pos"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in min_vars:
            return True
    return False


def _has_while_inner(tree: ast.AST) -> bool:
    """检测插入排序特征：内层是 while 循环（向后移动元素）。"""
    for outer in ast.walk(tree):
        if isinstance(outer, (ast.For, ast.While)):
            for inner in ast.walk(outer):
                if inner is not outer and isinstance(inner, ast.While):
                    return True
    return False


def _has_stalin(tree: ast.AST) -> bool:
    """检测斯大林排序特征：
    - 单层 for 循环（非嵌套）
    - 对 result[-1] 的比较
    - result.append(x) 调用
    - 没有嵌套循环、没有递归、没有交换
    """
    has_nested = _has_nested_loop(tree)
    has_rec = _has_recursion(tree)
    has_swp = _has_adjacent_swap(tree)

    # 斯大林排序不包含嵌套循环、递归、相邻交换
    if has_nested or has_rec or has_swp:
        return False

    # 检测 result[-1] 下标访问模式
    has_last_access = False
    has_append = False
    has_single_loop = False

    for node in ast.walk(tree):
        # 检测单层 for 循环
        if isinstance(node, ast.For):
            has_single_loop = True
        # 检测 result[-1] 或 arr[-1] 下标访问
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.UnaryOp) and isinstance(node.slice.op, ast.USub):
                if isinstance(node.slice.operand, ast.Constant) and node.slice.operand.value == 1:
                    has_last_access = True
        # 检测 .append() 调用
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "append":
                has_append = True

    return has_single_loop and has_last_access and has_append