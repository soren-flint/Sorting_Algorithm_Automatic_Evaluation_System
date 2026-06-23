"""测试排序定义判定器。"""
import pytest

from app.core.validator import (
    is_monotonic,
    is_permutation,
    is_subsequence,
    validate_sort,
    check_off_by_one,
)


class TestIsMonotonic:
    """有序性检查。"""

    def test_empty(self):
        assert is_monotonic([]) is True

    def test_single(self):
        assert is_monotonic([1]) is True

    def test_sorted(self):
        assert is_monotonic([1, 2, 3, 4, 5]) is True

    def test_equal_elements(self):
        assert is_monotonic([1, 1, 1, 2, 2]) is True

    def test_unsorted(self):
        assert is_monotonic([5, 2, 8, 1, 3]) is False

    def test_descending(self):
        assert is_monotonic([5, 4, 3, 2, 1]) is False


class TestIsPermutation:
    """排列性检查。"""

    def test_same(self):
        assert is_permutation([1, 2, 3], [3, 1, 2]) is True

    def test_different_length(self):
        assert is_permutation([1, 2], [1, 2, 3]) is False

    def test_duplicates(self):
        assert is_permutation([1, 1, 2], [2, 1, 1]) is True

    def test_missing_element(self):
        assert is_permutation([1, 3, 5], [3, 1, 5, 2]) is False

    def test_extra_element(self):
        assert is_permutation([1, 2, 3, 4], [1, 2, 3]) is False


class TestIsSubsequence:
    """子序列检查。"""

    def test_exact(self):
        assert is_subsequence([1, 2, 3], [1, 2, 3]) is True

    def test_delete_some(self):
        assert is_subsequence([1, 3, 5], [1, 3, 2, 5, 4]) is True

    def test_not_subsequence(self):
        # [1, 5, 3] 在原序列中 5 在 3 后，不构成子序列
        assert is_subsequence([1, 3], [3, 1, 2]) is False

    def test_empty_short(self):
        assert is_subsequence([], [1, 2, 3]) is True


class TestValidateSort:
    """排序规则判定。"""

    # --- strict 模式 ---
    def test_strict_correct(self):
        r = validate_sort([1, 2, 3], [3, 1, 2], "strict")
        assert r["passed"] is True

    def test_strict_not_monotonic(self):
        r = validate_sort([3, 1, 2], [3, 1, 2], "strict")
        assert r["passed"] is False
        assert "有序" in r["reason"]

    def test_strict_not_permutation(self):
        r = validate_sort([1, 2, 3], [1, 2, 3, 4], "strict")
        assert r["passed"] is False
        assert "排列" in r["reason"]

    def test_strict_stalin_should_fail(self):
        """关键教学点：严格模式下斯大林排序应失败。"""
        r = validate_sort([1, 3, 5], [3, 1, 5, 2], "strict")
        assert r["passed"] is False
        assert "排列" in r["reason"]

    # --- stalin 模式 ---
    def test_stalin_correct(self):
        r = validate_sort([1, 3, 5], [1, 3, 2, 5, 4], "stalin")
        assert r["passed"] is True

    def test_stalin_not_sorted(self):
        r = validate_sort([3, 1, 5], [1, 3, 2, 5, 4], "stalin")
        assert r["passed"] is False

    def test_stalin_not_subsequence(self):
        r = validate_sort([1, 5, 3], [1, 3, 2, 5, 4], "stalin")
        assert r["passed"] is False

    # --- stable 模式 ---
    def test_stable_correct(self):
        r = validate_sort([1, 2, 3], [3, 1, 2], "stable")
        assert r["passed"] is True

    # --- topk 模式 ---
    def test_topk_no_k(self):
        r = validate_sort([1, 2, 3, 5, 4], [3, 1, 2, 4, 5], "topk")
        assert r["passed"] is False

    def test_topk_with_k(self):
        r = validate_sort([1, 2, 3, 5, 4], [3, 1, 2, 4, 5], "topk", k=3)
        assert r["passed"] is True

    # --- 未知规则 ---
    def test_unknown_rule(self):
        r = validate_sort([1, 2], [1, 2], "unknown_rule")
        assert r["passed"] is False


class TestCheckOffByOne:
    """Off-by-one 检测。"""

    def test_one_more(self):
        hint = check_off_by_one([1, 2, 3, 4], [1, 2, 3])
        assert hint and "多" in hint

    def test_one_less(self):
        hint = check_off_by_one([1, 2], [1, 2, 3])
        assert hint and "少" in hint

    def test_reversed(self):
        hint = check_off_by_one([3, 2, 1], [1, 2, 3])
        assert hint and "逆序" in hint

    def test_no_issue(self):
        hint = check_off_by_one([1, 2, 3], [1, 2, 3])
        assert hint is None