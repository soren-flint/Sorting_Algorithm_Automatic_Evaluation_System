"""智能反馈引擎：traceback 匹配 + 静态结构检查 + 语法预扫描 + 算法定制提示。

三层诊断策略：
  1. traceback 规则匹配（运行时异常 → 精准提示）
  2. 静态结构检查（AST 解析 + 正则预扫描 → 语法/结构问题）
  3. 按算法类型定制反馈（上下文感知的专属提示）
"""

import ast
import re


# ── 排序场景 traceback 规则库（V2：按算法类型定制） ──

SORT_TRACEBACK_PATTERNS = {
    "IndexError": [
        {
            "pattern": "list index out of range",
            "hint": "下标越界：你访问了列表外的位置。检查循环边界。",
            "algo_hints": {
                "bubble": "冒泡排序下标越界 —— 检查内层循环范围 range(n-1-i)，当 i=0 时 j 最大取 n-2，arr[j+1] 取到最后一个元素 n-1",
                "select": "选择排序下标越界 —— 检查内层循环范围 range(i+1, n)，确保 arr[j] 不会超出数组",
                "insert": "插入排序下标越界 —— 检查 while 循环中 j 的递减，确保 arr[j] 不取负下标；外循环应从 range(1, n) 开始",
                "quick": "快速排序下标越界 —— 检查递归终止条件是否处理空数组（应使用 len(arr)<=1 而非 ==1，空数组取 pivot 会崩溃）",
                "merge": "归并排序下标越界 —— 检查 L[i:] 和 R[j:] 的索引指针 i/j 是否正确递增；合并剩余元素时不要超出子数组范围",
                "heap": "堆排序下标越界 —— 检查 heapify 中 left=2*i+1 和 right=2*i+2 是否超出堆大小 n",
            },
        }
    ],
    "IndentationError": [
        {
            "pattern": "expected an indented block",
            "hint": "缩进错误：代码块缺少缩进。检查 if/for/while/def 后面的行是否用 4 个空格或 Tab 缩进了。",
        },
        {
            "pattern": "unexpected indent",
            "hint": "缩进错误：多出了不该有的缩进。检查是否有混用空格和 Tab。",
        },
        {
            "pattern": "unindent does not match",
            "hint": "缩进错误：缩进级别不匹配。可能是混用了 Tab 和空格，或某行缩进量与上一级不一致。",
        },
    ],
    "NameError": [
        {
            "pattern": "name '(.+)' is not defined",
            "hint_match": "变量 '{}' 未定义 —— 检查是否有拼写错误，如把 len 写成 lne，或忘记初始化变量。",
        }
    ],
    "TypeError": [
        {
            "pattern": "not supported between instances of",
            "hint": "类型比较错误：排序时比较了不同类型的数据（如整数和字符串）—— 检查输入数组是否混合了不同数据类型。",
        },
        {
            "pattern": "object is not subscriptable",
            "hint": "类型错误：对不支持索引的对象用了 []。可能把整数或 None 当作列表来索引了。",
        },
        {
            "pattern": "can't multiply sequence by non-int of type",
            "hint": "类型错误：序列乘法类型不匹配 —— 可能是把列表乘了非整数，检查循环中的乘法操作。",
        },
    ],
    "RecursionError": [
        {
            "pattern": "maximum recursion depth exceeded",
            "hint": "递归过深：检查递归终止条件是否正确。常见问题：忘记写终止条件，或终止条件永远达不到（如永远拆不出长度为 1 的子数组）。",
        }
    ],
    "UnboundLocalError": [
        {
            "pattern": "referenced before assignment",
            "hint": "变量引用错误：某变量在使用前未被赋值。检查分支逻辑 —— 可能某个分支里没有给变量赋值就直接使用了。",
        }
    ],
    "ValueError": [
        {
            "pattern": "not enough values to unpack",
            "hint": "解包错误：元组/列表解包时元素数量不匹配。检查交换语句 arr[i], arr[j] = arr[j], arr[i] 两边元素数是否一致。",
        }
    ],
    "SyntaxError": [
        {
            "pattern": "invalid syntax",
            "hint": "语法错误 —— 检查该行及上一行的冒号、括号、引号是否成对闭合。",
        }
    ],
}


# ── 异常类型 → 中文显示名映射 ──
_EXC_DISPLAY_NAMES: dict[str, str] = {
    "IndexError": "下标越界",
    "IndentationError": "缩进错误",
    "NameError": "变量未定义",
    "TypeError": "类型比较错误",
    "RecursionError": "递归过深",
    "UnboundLocalError": "变量引用错误",
    "ValueError": "解包错误",
    "SyntaxError": "语法错误",
}


def _match_traceback(stderr: str) -> dict | None:
    """将 stderr 与规则库匹配，返回最匹配的提示。

    Returns:
        {"type": str, "hint": str} | None
        type 为中文显示名（如 "下标越界"）。
    """
    for exc_type, rules in SORT_TRACEBACK_PATTERNS.items():
        if exc_type not in stderr:
            continue
        for rule in rules:
            m = re.search(rule["pattern"], stderr)
            if m:
                hint = rule.get("hint", "")
                if "hint_match" in rule and m.groups():
                    hint = rule["hint_match"].format(*m.groups())
                display_type = _EXC_DISPLAY_NAMES.get(exc_type, exc_type)
                return {"type": display_type, "hint": hint}
    return None


def _algo_key(recognized: str) -> str:
    """从识别结果提取纯 key。"""
    if not recognized:
        return ""
    return recognized.split("(")[0].strip().lower() if "(" in recognized else recognized.strip().lower()


def diagnose(code: str, run_result: dict, recognized_algo: str = "") -> dict | None:
    """智能诊断：超时 → traceback → NameError 特殊处理 → 静态检查。

    Args:
        code: 用户代码。
        run_result: sandbox 返回结果 {"returncode": int, "stderr": str, "stdout": str, "timed_out": bool}。
        recognized_algo: 算法识别结果，如 "quick (快速排序)"。

    Returns:
        {"type": str, "hint": str, "line": int|None} | None
    """
    stderr = run_result.get("stderr", "") or ""
    algo = _algo_key(recognized_algo)

    # 0. 超时优先（无 traceback 可匹配）
    if run_result.get("timed_out"):
        return {
            "type": "超时",
            "hint": "代码执行超时（超过 5 秒）——检查循环终止条件，排查是否存在死循环",
            "line": None,
        }

    # 1. traceback 匹配（含算法定制提示）
    match = _match_traceback(stderr)
    if match:
        hint = match["hint"]
        exc_type = match["type"]

        # 如果有算法定制提示，追加到通用提示后面
        for raw_type, rules in SORT_TRACEBACK_PATTERNS.items():
            display = _EXC_DISPLAY_NAMES.get(raw_type, raw_type)
            if exc_type == display:
                for rule in rules:
                    if "algo_hints" in rule and algo in rule["algo_hints"]:
                        hint += "\n" + rule["algo_hints"][algo]
                        break
                break

        # NameError 特殊处理：sort / temp / 无函数
        if exc_type == "变量未定义" and "NameError" in stderr:
            name_match = re.search(r"name '(\w+)' is not defined", stderr)
            if name_match:
                var_name = name_match.group(1)
                if var_name == "sort":
                    # 检查代码中是否定义了其他函数（函数名错误）
                    has_other_func = bool(re.search(r'\bdef\s+(\w+)\s*\(', code))
                    if has_other_func:
                        func_match = re.search(r'\bdef\s+(\w+)\s*\(', code)
                        other_name = func_match.group(1) if func_match else "其他函数"
                        return {
                            "type": "函数名错误",
                            "hint": f"NameError: name 'sort' is not defined —— 你定义的函数名为 '{other_name}'，但题目要求函数名必须为 sort。请将 def {other_name}(arr): 改为 def sort(arr):",
                            "line": None,
                        }
                    else:
                        # 无任何函数定义
                        return {
                            "type": "缺少函数",
                            "hint": "NameError: name 'sort' is not defined —— 你需要定义一个名为 sort 的函数，格式为 def sort(arr): ... return arr",
                            "line": None,
                        }
                elif var_name in ("temp", "tmp"):
                    return {
                        "type": "多余变量",
                        "hint": f"NameError: name '{var_name}' is not defined —— 交换两个变量不需要临时变量：arr[i], arr[j] = arr[j], arr[i] 一行就能完成交换。删除 {var_name} 变量试试。",
                        "line": None,
                    }

        # 提取行号
        line_match = re.search(r'line (\d+)', stderr)
        return {
            "type": exc_type,
            "hint": hint,
            "line": int(line_match.group(1)) if line_match else None,
        }

    # 2. 静态检查兜底（语法/结构层面）
    static_issues = static_check_sort(code)
    if static_issues:
        first = static_issues[0]
        return {
            "type": first.get("type", "结构提醒"),
            "hint": first["hint"],
            "line": first.get("line"),
        }

    return None


# ── 正则预扫描：在 AST 解析前捕获多个语法错误 ──

_SYNTAX_PATTERNS: list[tuple[str, str]] = [
    # (正则, 提示模板)
    # 函数/类定义缺冒号（处理已剥离注释的代码行）
    (r'^\s*def\s+\w+\s*\([^)]*\)\s*(?<!:)$',
     "函数定义缺少冒号 : —— 第 {line} 行: def 语句末尾需要冒号"),
    # if/elif/while/for/else 缺冒号（处理已剥离注释的代码行）
    (r'^\s*(if|elif|while|for|else)\s+.*(?<!:)$',
     "语句缺少冒号 : —— 第 {line} 行: {match} 语句末尾需要冒号"),
    # 赋值缺等号（如 pivot arr[...]）
    (r'^\s+(\w+)\s+(arr\[.+\])\s*$',
     "赋值缺少 = —— 第 {line} 行: '{match}' 可能是赋值语句，缺少等号"),
    # return 语句中 list 拼接缺 + 号（如 sort(left) mid sort(right)）
    (r'return\s+\w+\([^)]+\)\s+\w+\s+\w+\([^)]+\)',
     "return 语句缺少运算符 —— 第 {line} 行: 函数调用之间缺少 + 或其他运算符"),
    # 关键字拼写错误
    (r'\bretrun\b',
     "关键字拼写错误 —— 第 {line} 行: 'retrun' 应为 'return'"),
    (r'\bdef\s+retrun\b',
     "关键字拼写错误 —— 第 {line} 行: 可能是 return 写成了 retrun"),
    (r'\bels\s*:',
     "关键字拼写错误 —— 第 {line} 行: 'els' 应为 'else'"),
    # range 参数缺少逗号或运算符
    (r'range\(\s*\w+\s+\w+\s*\)',
     "range 参数缺少逗号 —— 第 {line} 行: range() 的参数需要逗号分隔，如 range(i+1, n)"),
    # 列表推导式未闭合（左括号多于右括号）
    (r'^\s*(\w+)\s*=\s*\[.*(?<!\])\s*$',
     ""),  # 占位，由后面括号计数处理
]


def _strip_inline_comment(line: str) -> str:
    """剥离行内注释（# 及之后内容），保留字符串内的 #。"""
    in_string = False
    string_char = None
    for j, ch in enumerate(line):
        if ch in ('"', "'") and not in_string:
            in_string = True
            string_char = ch
        elif ch == string_char and in_string:
            in_string = False
            string_char = None
        elif ch == '#' and not in_string:
            return line[:j].rstrip()
    return line.rstrip()


def _quick_syntax_scan(code: str) -> list[dict]:
    """在 AST 解析前进行多遍正则轻量扫描，捕获所有语法错误。

    与 ast.parse 互补：ast.parse 遇第一个错误即停，
    正则扫描可检测整段代码中多个常见语法问题。

    Returns:
        list[dict]: 每项 {"type": "语法错误", "line": int|None, "hint": str}
    """
    issues: list[dict] = []
    lines = code.split("\n")

    for regex, template in _SYNTAX_PATTERNS:
        if not template:  # 跳过占位
            continue
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # 剥离行内注释，避免误报（如 "if x>0:  # 注释" 被判定为缺冒号）
            check_line = _strip_inline_comment(line)
            if not check_line.strip() or check_line.strip().startswith("#"):
                continue
            m = re.search(regex, check_line)
            if m:
                match_text = m.group(0).strip()[:60]
                hint = template.format(line=i, match=match_text)
                issues.append({
                    "type": "语法错误",
                    "line": i,
                    "hint": hint,
                })

    # 括号闭合检查
    bracket_issues = _check_bracket_balance(lines)
    issues.extend(bracket_issues)

    # 去重（同一行同类型只保留一条）
    seen = set()
    unique_issues = []
    for iss in issues:
        key = (iss["type"], iss["line"])
        if key not in seen:
            seen.add(key)
            unique_issues.append(iss)

    return unique_issues


def _check_bracket_balance(lines: list[str]) -> list[dict]:
    """检查每行的括号闭合情况。"""
    issues = []
    bracket_pairs = {"(": ")", "[": "]", "{": "}"}

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for open_b, close_b in bracket_pairs.items():
            open_count = stripped.count(open_b)
            close_count = stripped.count(close_b)
            if open_count > close_count:
                # 排除字符串内的情况（简单启发式）
                in_string = False
                for ch in stripped:
                    if ch in ('"', "'"):
                        in_string = not in_string
                if not in_string:
                    issues.append({
                        "type": "语法错误",
                        "line": i,
                        "hint": f"括号未闭合 —— 第 {i} 行: {open_count - close_count} 个 '{open_b}' 缺少对应的 '{close_b}'。例如列表推导式 [{open_b}... 缺少闭合 {close_b}。",
                    })
                    break  # 一行只报一个括号问题

    return issues


# ── 静态结构检查（V2：扩充检查规则） ──

def static_check_sort(code: str, tree: ast.AST | None = None) -> list[dict]:
    """静态检查排序代码的结构/语法问题。

    Args:
        code: 用户源代码。
        tree: 预解析的 AST（可选）。传入后跳过 ast.parse。

    Returns:
        list[dict]: 每项 {"type": str, "line": int|None, "hint": str}
    """
    issues: list[dict] = []

    # ── 0. 多遍正则语法预扫描（在 ast.parse 之前） ──
    syntax_issues = _quick_syntax_scan(code)
    issues.extend(syntax_issues)

    # ── 1. AST 语法检查 ──
    if tree is None:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            # 补充 ast 层面的语法错误（可能与前扫描重复，但 line 更精确）
            hint = f"语法错误：代码存在语法错误。请检查第 {e.lineno} 行附近的括号、冒号、缩进。详细信息: {e.msg}"
            # 避免与正则扫描完全重复
            if not any(i["line"] == e.lineno and i["type"] == "语法错误" for i in issues):
                issues.append({
                    "type": "语法错误",
                    "line": e.lineno,
                    "hint": hint,
                })
            return issues  # 语法错误下无法进行后续结构分析

    code_lines = code.split("\n")

    # ── 2. 安全：危险函数检查 ──
    DANGEROUS_PATTERNS = [
        (r'\beval\s*\(', "eval()"),
        (r'\bexec\s*\(', "exec()"),
        (r'\bcompile\s*\(', "compile()"),
        (r'\b__import__\s*\(', "__import__()"),
        (r'\bopen\s*\(', "open() —— 排序练习不需要文件操作"),
        (r'\bos\.system\b', "os.system()"),
        (r'\bsubprocess\b', "subprocess 调用"),
    ]
    for i, line in enumerate(code_lines, 1):
        for pattern, name in DANGEROUS_PATTERNS:
            if re.search(pattern, line) and not line.strip().startswith("#"):
                issues.append({
                    "type": "安全警告",
                    "line": i,
                    "hint": f"检测到不允许的函数调用: {name}。排序练习中不应使用此函数。",
                })

    # ── 3. 函数定义检查 ──
    has_sort_func = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "sort":
                has_sort_func = True
                # 3a. 参数数量检查
                args = node.args
                total_params = len(args.args) + len(args.posonlyargs)
                if total_params != 1:
                    issues.append({
                        "type": "结构提醒",
                        "line": node.lineno,
                        "hint": f"sort 函数应有 1 个参数（接收数组），当前有 {total_params} 个参数",
                    })
                # 3b. 函数体空检查
                if len(node.body) == 0:
                    issues.append({
                        "type": "结构提醒",
                        "line": node.lineno,
                        "hint": "sort 函数体为空 —— 请实现排序逻辑",
                    })
                elif len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    issues.append({
                        "type": "结构提醒",
                        "line": node.lineno,
                        "hint": "sort 函数体只有 pass —— 请实现排序逻辑",
                    })
                # 3c. 不可达代码检测：函数首行即 return
                if len(node.body) >= 1 and isinstance(node.body[0], ast.Return):
                    # 检查 return 是否有条件（if return 是正常的递归终止）
                    if not _is_conditional_return(node.body[0], node):
                        issues.append({
                            "type": "结构提醒",
                            "line": node.body[0].lineno,
                            "hint": "函数首行即无条件 return —— 后续代码将永远不会执行（不可达代码）。递归终止条件应放在 if len(arr)<=1 分支内。",
                        })
                # 3d. 是否有 return 语句
                has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
                if not has_return:
                    issues.append({
                        "type": "结构提醒",
                        "line": node.lineno,
                        "hint": "sort 函数缺少 return 语句 —— 排序函数需要返回排序后的数组",
                    })
                break

    if not has_sort_func:
        # 检查是否有其他函数定义（有函数但名字不对 → 函数名错误）
        other_func_match = re.search(r'\bdef\s+(\w+)\s*\(', code)
        if other_func_match:
            other_name = other_func_match.group(1)
            issues.append({
                "type": "函数名错误",
                "line": None,
                "hint": f"定义了函数 '{other_name}'，但题目要求函数名必须为 sort。请将 def {other_name}(arr): 改为 def sort(arr):",
            })
        else:
            issues.append({
                "type": "结构提醒",
                "line": None,
                "hint": "未找到 sort(arr) 函数定义 —— 题目要求函数名必须为 sort",
            })

    # ── 4. 递归终止条件检查 ──
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 找到所有 if len(arr) ... return 的模式
            for child in node.body:
                if isinstance(child, ast.If):
                    test_str = _safe_unparse(child.test)
                    if "len" in test_str and "arr" in test_str:
                        # 检查是否只处理 ==1 而没处理空数组
                        if "== 1" in test_str and "<=" not in test_str and "< 2" not in test_str:
                            issues.append({
                                "type": "结构提醒",
                                "line": child.lineno,
                                "hint": "递归终止条件可能不完整：使用 len(arr)==1 仅处理单元素数组，空列表会缺少保护。建议改为 len(arr)<=1 以同时处理空数组。",
                            })
                        break  # 只检查第一个终止条件

    # ── 5. 循环边界合理性检查 ──
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            if _is_range_call(node.iter):
                range_args = node.iter.args
                # 需要至少 2 个参数（start, stop）才检查
                if len(range_args) >= 2:
                    # arg1 为 n-1 的情况（可能遗漏末尾元素）
                    if isinstance(range_args[1], ast.BinOp):
                        if isinstance(range_args[1].op, ast.Sub):
                            right_val = _get_constant(range_args[1].right)
                            if right_val == 1:
                                issues.append({
                                    "type": "结构提醒",
                                    "line": node.lineno,
                                    "hint": f"循环边界 range(..., n-1) 遗漏了最后一个元素（下标 n-1）。排序中内循环通常到 n。",
                                })

    return issues


# ── AST/正则辅助函数 ──

def _is_conditional_return(ret_node: ast.Return, func_node: ast.AST) -> bool:
    """判断 return 语句是否在条件分支内（如 if len(arr)<=1: return）。"""
    for node in ast.walk(func_node):
        if isinstance(node, ast.If):
            for child in ast.walk(node):
                if child is ret_node:
                    return True
    return False


def _is_range_call(node: ast.AST) -> bool:
    """判断 AST 节点是否为 range(...) 调用。"""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "range"
    )


def _get_constant(node: ast.AST):
    """获取常量值，非常量返回 None。"""
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _safe_unparse(node: ast.AST) -> str:
    """安全地将 AST 节点转回字符串。"""
    try:
        if hasattr(ast, 'unparse'):
            return ast.unparse(node)
        return str(node)
    except Exception:
        return "<expr>"