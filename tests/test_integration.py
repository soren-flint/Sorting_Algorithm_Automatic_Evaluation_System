"""集成测试：端到端评测流程。"""
import json

from app.core.comparator import compare_outputs
from app.core.feedback import diagnose, static_check_sort
from app.core.recognizer import recognize_algorithm
from app.core.sandbox import run_code
from app.core.step_collector import collect_steps
from app.core.validator import validate_sort


# 用于评测的完整代码模板（含 stdin 读取 + sort 调用 + stdout 输出）
WRAPPER_TEMPLATE = '''
import json, sys

{user_code}

if __name__ == "__main__":
    input_data = json.loads(sys.stdin.read())
    result = sort(input_data)
    print(json.dumps(result))
'''


class TestIntegration:
    """端到端评测集成测试。"""

    # ---- 正确代码全流程 ----

    def test_full_pipeline_bubble_pass(self):
        """冒泡排序：提交正确代码 → 算法识别 → 沙箱执行 → 判定通过。"""
        code = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''
        wrapped = WRAPPER_TEMPLATE.format(user_code=code)

        # 步骤 1: 算法识别
        algo = recognize_algorithm(code)
        assert "bubble" in algo

        # 步骤 2: AST 静态检查
        issues = static_check_sort(code)
        danger = [i for i in issues if i["type"] == "安全警告"]
        assert len(danger) == 0

        # 步骤 3: 沙箱执行
        result = run_code(wrapped, "[5,2,8,1,3]")
        assert result["returncode"] == 0
        assert not result["timed_out"]

        # 步骤 4: 比对判定
        cmp = compare_outputs(
            result["stdout"].strip(), "[1,2,3,5,8]", [5, 2, 8, 1, 3], "strict"
        )
        assert cmp["passed"] is True

        # 步骤 5: 步骤采集
        steps = collect_steps(code, [5, 2, 8, 1, 3])
        assert len(steps) > 1

    def test_full_pipeline_quick_pass(self):
        """快排：递归代码全流程通过。"""
        code = '''
def sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr)//2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return sort(left) + mid + sort(right)
'''
        wrapped = WRAPPER_TEMPLATE.format(user_code=code)

        algo = recognize_algorithm(code)
        assert "quick" in algo

        result = run_code(wrapped, "[5,4,3,2,1]")
        assert result["returncode"] == 0

        cmp = compare_outputs(
            result["stdout"].strip(), "[1,2,3,4,5]", [5, 4, 3, 2, 1], "strict"
        )
        assert cmp["passed"] is True

    # ---- 错误代码全流程 ----

    def test_syntax_error_flow(self):
        """语法错误：识别 → 静态检查捕获 → 不进入沙箱。"""
        code = "def sort(:"

        algo = recognize_algorithm(code)
        assert "unknown" in algo or "语法" in algo

        issues = static_check_sort(code)
        assert len(issues) > 0

    def test_timeout_flow(self):
        """死循环：沙箱超时 → 反馈引擎识别。"""
        code = '''
def sort(arr):
    while True:
        pass
'''
        wrapped = WRAPPER_TEMPLATE.format(user_code=code)
        result = run_code(wrapped, "[1,2]", timeout=1.0)
        assert result["timed_out"] is True

        diag = diagnose(code, result)
        assert diag is not None
        assert diag["type"] == "超时"

    def test_logic_error_flow(self):
        """逻辑错误：输出错误 → 反馈给出具体原因。"""
        code = '''
def sort(arr):
    # BUG: 返回逆序
    return list(reversed(sorted(arr)))
'''
        wrapped = WRAPPER_TEMPLATE.format(user_code=code)
        result = run_code(wrapped, "[3,1,2]")

        cmp = compare_outputs(
            result["stdout"].strip(), None, [3, 1, 2], "strict"
        )
        assert cmp["passed"] is False
        assert "有序" in cmp["reason"]

    # ---- 斯大林排序全流程 ----

    def test_stalin_sort_full_flow(self):
        """斯大林排序：stalin 规则 + 步骤采集。"""
        code = '''
def sort(arr):
    if not arr:
        return []
    result = [arr[0]]
    for x in arr[1:]:
        if x >= result[-1]:
            result.append(x)
    return result
'''
        wrapped = WRAPPER_TEMPLATE.format(user_code=code)
        result = run_code(wrapped, "[1,3,2,5,4]")
        assert result["returncode"] == 0

        # stalin 规则判定：无期望输出，validate_sort 判定
        actual = json.loads(result["stdout"])
        # 斯大林排序：输出可能为 [1,3,5]（删了 2 和 4）
        v_result = validate_sort(actual, [1, 3, 2, 5, 4], "stalin")
        assert v_result["passed"] is True

    # ---- 空数组 / 单元素边界 ----

    def test_empty_array_flow(self):
        """空数组全流程。"""
        code = '''
def sort(arr):
    return arr
'''
        wrapped = WRAPPER_TEMPLATE.format(user_code=code)
        result = run_code(wrapped, "[]")
        assert result["returncode"] == 0

        cmp = compare_outputs(
            result["stdout"].strip(), "[]", [], "strict"
        )
        assert cmp["passed"] is True

    def test_single_element_flow(self):
        """单元素全流程。"""
        code = '''
def sort(arr):
    return arr
'''
        wrapped = WRAPPER_TEMPLATE.format(user_code=code)
        result = run_code(wrapped, "[1]")
        assert result["returncode"] == 0

        cmp = compare_outputs(
            result["stdout"].strip(), "[1]", [1], "strict"
        )
        assert cmp["passed"] is True
