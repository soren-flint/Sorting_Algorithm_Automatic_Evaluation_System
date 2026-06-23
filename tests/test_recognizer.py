"""测试算法识别器。"""
from app.core.recognizer import recognize_algorithm


class TestRecognizer:
    """算法识别测试。"""

    def test_recognize_bubble(self):
        code = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''
        result = recognize_algorithm(code)
        assert "bubble" in result

    def test_recognize_quick(self):
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
        result = recognize_algorithm(code)
        assert "quick" in result

    def test_recognize_merge(self):
        code = '''
def sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = sort(arr[:mid])
    right = sort(arr[mid:])
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
'''
        result = recognize_algorithm(code)
        assert "merge" in result

    def test_recognize_select(self):
        code = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr
'''
        result = recognize_algorithm(code)
        # select 或 select/insert 都可接受
        assert "select" in result

    def test_recognize_insert(self):
        code = '''
def sort(arr):
    n = len(arr)
    for i in range(1, n):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr
'''
        result = recognize_algorithm(code)
        assert "insert" in result or "select/insert" in result

    def test_syntax_error(self):
        """语法错误的代码应返回 unknown。"""
        result = recognize_algorithm("def sort(:")
        assert "unknown" in result or "语法" in result

    def test_empty_code(self):
        """空代码。"""
        result = recognize_algorithm("")
        assert "unknown" in result
