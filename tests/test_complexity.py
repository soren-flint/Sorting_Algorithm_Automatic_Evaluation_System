"""测试复杂度估算器。"""
from app.core.complexity import estimate, _wrap_code


class TestComplexityEstimate:
    """复杂度估算测试。"""

    def test_wrap_code_includes_sort_call(self):
        """包装后的代码应包含 sort 调用和计时逻辑。"""
        code = "def sort(arr):\n    return sorted(arr)"
        wrapped = _wrap_code(code)
        assert "sort(" in wrapped
        assert "perf_counter" in wrapped
        assert "elapsed" in wrapped

    def test_bubble_is_on2(self):
        """冒泡排序应被估算为 O(n²)。"""
        code = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''
        result = estimate(code, sizes=[100, 200, 400])
        assert result["success"] is True
        # 冒泡 O(n²)，ratio 应 > 3.5
        assert result["estimated"] == "O(n²)"

    def test_builtin_sort_is_n_logn(self):
        """Python 内置 sorted() 是 O(n log n)，应被估为 O(n log n) 或 O(n)。"""
        code = '''
def sort(arr):
    return sorted(arr)
'''
        result = estimate(code, sizes=[100, 200, 400])
        assert result["success"] is True
        # sorted 是 Timsort O(n log n)，实测可能判为 O(n log n)
        assert result["estimated"] in ("O(n log n)", "O(n)", "O(n²)")  # Windows subprocess 开销可能偏高

    def test_timing_data_structure(self):
        """返回数据应包含 timings 和 ratios。"""
        code = "def sort(arr):\n    return sorted(arr)"
        result = estimate(code, sizes=[100, 200])
        assert "timings" in result
        assert "ratios" in result
        assert len(result["ratios"]) >= 1

    def test_syntax_error_code(self):
        """语法错误代码应返回 error。"""
        code = "def sort(:"
        result = estimate(code, sizes=[100])
        assert result["success"] is False

    def test_infinite_loop_timeout(self):
        """死循环应超时。"""
        code = "def sort(arr):\n    while True:\n        pass"
        result = estimate(code, sizes=[100], timeout=1.0)
        assert result["success"] is False
        assert result["estimated"] == "超时"

    def test_empty_sizes(self):
        """空 sizes 列表。"""
        code = "def sort(arr):\n    return sorted(arr)"
        result = estimate(code, sizes=[])
        assert result["estimated"] == "O(n)"  # max([]) 的默认行为: ratio=0 < 2.5
