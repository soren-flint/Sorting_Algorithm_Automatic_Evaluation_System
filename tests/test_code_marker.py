"""测试 AST 代码行标记器。"""
import pytest

from app.core.code_marker import mark_code


class TestCodeMarker:
    """代码行标记测试。"""

    # ── 冒泡排序 ──

    def test_mark_bubble_standard(self):
        """标准冒泡排序应标记所有关键行。"""
        code = '''def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr'''
        result = mark_code(code, "bubble")
        assert result is not None
        lines = result["lines"]
        assert "outer_loop" in lines
        assert "compare" in lines
        assert "swap" in lines
        assert "return" in lines

    def test_mark_bubble_returns_code_lines(self):
        """应返回 code_lines 列表。"""
        code = '''def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr'''
        result = mark_code(code, "bubble")
        assert "code_lines" in result
        assert isinstance(result["code_lines"], list)
        assert len(result["code_lines"]) > 0

    def test_mark_bubble_no_sort_function(self):
        """没有 sort 函数的代码应返回 None。"""
        code = "x = 1\ny = 2"
        result = mark_code(code, "bubble")
        assert result is None

    def test_mark_bubble_syntax_error(self):
        """语法错误的代码应返回 None。"""
        code = "def sort(:\n    pass"
        result = mark_code(code, "bubble")
        assert result is None

    # ── 选择排序 ──

    def test_mark_select_standard(self):
        """标准选择排序应标记关键行。"""
        code = '''def sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr'''
        result = mark_code(code, "select")
        assert result is not None
        lines = result["lines"]
        assert "outer_loop" in lines
        assert "return" in lines

    # ── 插入排序 ──

    def test_mark_insert_standard(self):
        """标准插入排序应标记关键行。"""
        code = '''def sort(arr):
    n = len(arr)
    for i in range(1, n):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr'''
        result = mark_code(code, "insert")
        assert result is not None
        lines = result["lines"]
        assert "outer_loop" in lines

    # ── 快速排序 ──

    def test_mark_quick_standard(self):
        """标准快速排序应标记关键行。"""
        code = '''def sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return sort(left) + mid + sort(right)'''
        result = mark_code(code, "quick")
        assert result is not None

    # ── 归并排序 ──

    def test_mark_merge_standard(self):
        """标准归并排序应标记关键行。"""
        code = '''def sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    L = sort(arr[:mid])
    R = sort(arr[mid:])
    result, i, j = [], 0, 0
    while i < len(L) and j < len(R):
        if L[i] <= R[j]:
            result.append(L[i]); i += 1
        else:
            result.append(R[j]); j += 1
    return result + L[i:] + R[j:]'''
        result = mark_code(code, "merge")
        assert result is not None

    # ── 堆排序 ──

    def test_mark_heap_standard(self):
        """标准堆排序应标记关键行。"""
        code = '''def sort(arr):
    def heapify(a, n, i):
        largest = i
        l, r = 2 * i + 1, 2 * i + 2
        if l < n and a[l] > a[largest]: largest = l
        if r < n and a[r] > a[largest]: largest = r
        if largest != i:
            a[i], a[largest] = a[largest], a[i]
            heapify(a, n, largest)
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1): heapify(arr, n, i)
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)
    return arr'''
        result = mark_code(code, "heap")
        assert result is not None

    # ── 未知算法 ──

    def test_mark_unknown_algo_returns_none(self):
        """未知算法类型应返回 None。"""
        code = "def sort(arr):\n    return sorted(arr)"
        result = mark_code(code, "unknown_algo")
        assert result is None