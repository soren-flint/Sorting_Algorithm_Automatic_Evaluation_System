"""测试代码查重引擎。"""
import pytest

from app.core.similarity import _tokenize, detect, similarity


class TestSimilarity:
    """相似度检测测试。"""

    def test_identical_code(self):
        """完全相同的代码相似度应为 1.0。"""
        code = "def sort(a):\n    return sorted(a)"
        assert similarity(code, code) == 1.0

    def test_completely_different(self):
        """完全不同的代码相似度应低。"""
        a = "def sort(a):\n    return sorted(a)"
        b = "class Foo:\n    def bar(self):\n        pass"
        s = similarity(a, b)
        assert s < 0.5

    def test_rename_variables_resistant(self):
        """仅改变量名应保持高相似度（AST 结构相同）。"""
        a = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''
        b = '''
def sort(xyz):
    m = len(xyz)
    for p in range(m):
        for q in range(m - 1 - p):
            if xyz[q] > xyz[q + 1]:
                xyz[q], xyz[q + 1] = xyz[q + 1], xyz[q]
    return xyz
'''
        s = similarity(a, b)
        assert s > 0.85, f"Expected >0.85, got {s}"

    def test_bubble_vs_quick(self):
        """冒泡 vs 快排：AST 结构共享 Python 模式，相似度客观偏高。
        改名对相似度 (~1.0) 远超不同算法对。"""
        bubble = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''
        quick = '''
def sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[0]
    left = [x for x in arr[1:] if x <= pivot]
    right = [x for x in arr[1:] if x > pivot]
    return sort(left) + [pivot] + sort(right)
'''
        s_bq = similarity(bubble, quick)
        # 改名对（AST 结构相同）相似度应 > 不同算法对
        bubble2 = '''
def sort(lst):
    m = len(lst)
    for i in range(m):
        for j in range(m - 1 - i):
            if lst[j] > lst[j + 1]:
                lst[j], lst[j + 1] = lst[j + 1], lst[j]
    return lst
'''
        s_bb = similarity(bubble, bubble2)
        assert s_bb > s_bq, f"改名对 {s_bb} 应 > 不同算法对 {s_bq}"

    def test_syntax_error_code(self):
        """语法错误代码退化到词法 token，相同代码≈1.0。"""
        s = similarity("def sort(:", "def sort(:")
        assert s == pytest.approx(1.0)

    def test_syntax_error_vs_normal(self):
        """语法错 vs 正常代码应低相似度。"""
        s = similarity("def sort(:", "def sort(a): return sorted(a)")
        assert s < 0.5


class TestDetect:
    """批量检测测试。"""

    def test_no_pairs_below_threshold(self):
        """无相似对时返回空列表。"""
        class FakeSub:
            def __init__(self, user, code, sid):
                self.user = user
                self.code = code
                self.id = sid

        class FakeUser:
            def __init__(self, name):
                self.username = name

        subs = [
            FakeSub(FakeUser("a"), "def sort(a): return sorted(a)", 1),
            FakeSub(FakeUser("b"), "class X: pass", 2),
        ]
        result = detect(subs, threshold=0.85)
        assert len(result) == 0

    def test_identical_pair_detected(self):
        """相同代码对应被检出。"""
        class FakeSub:
            def __init__(self, user, code, sid):
                self.user = user
                self.code = code
                self.id = sid

        class FakeUser:
            def __init__(self, name):
                self.username = name

        code = "def sort(a): return sorted(a)"
        subs = [
            FakeSub(FakeUser("a"), code, 1),
            FakeSub(FakeUser("b"), code, 2),
        ]
        result = detect(subs, threshold=0.85)
        assert len(result) == 1
        assert result[0]["similarity"] == 1.0

    def test_sorted_by_similarity_desc(self):
        """结果应按相似度降序排列。"""
        class FakeSub:
            def __init__(self, user, code, sid):
                self.user = user
                self.code = code
                self.id = sid

        class FakeUser:
            def __init__(self, name):
                self.username = name

        import copy
        bubble = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''
        bubble2 = bubble.replace("arr", "lst")
        quick = '''
def sort(arr):
    if len(arr) <= 1: return arr
    pivot = arr[0]
    return sort([x for x in arr[1:] if x <= pivot]) + [pivot] + sort([x for x in arr[1:] if x > pivot])
'''
        subs = [
            FakeSub(FakeUser("a"), bubble, 1),
            FakeSub(FakeUser("b"), bubble2, 2),
            FakeSub(FakeUser("c"), quick, 3),
        ]
        result = detect(subs, threshold=0.5)
        # 应至少有 bubble-bubble2 对，且 sim 最高
        assert len(result) >= 1
        assert result[0]["similarity"] >= 0.9
