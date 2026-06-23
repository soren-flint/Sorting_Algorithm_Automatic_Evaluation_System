"""测试算法模拟器。"""
import pytest

from app.core.algo_simulators import simulate


class TestAlgoSimulators:
    """算法模拟器测试。"""

    def _check_steps(self, steps):
        """验证步骤基本结构。"""
        assert len(steps) > 1, "应产生多个步骤"
        for s in steps:
            assert "seq" in s
            assert "array_state" in s
            assert "op" in s
            assert "i" in s
            assert "j" in s
            assert "note" in s
            assert "round" in s

    def _check_final_sorted(self, steps, original):
        """验证最终数组有序。"""
        final = steps[-1]["array_state"]
        assert final == sorted(original), f"{final} != {sorted(original)}"

    # ── 冒泡排序 ──

    def test_bubble_simulates(self):
        """冒泡排序模拟应产生 compare/swap 步骤。"""
        steps = simulate("bubble", [5, 3, 1, 2, 4])
        self._check_steps(steps)
        self._check_final_sorted(steps, [5, 3, 1, 2, 4])
        ops = [s["op"] for s in steps]
        assert "compare" in ops
        assert "swap" in ops
        assert "init" in ops
        assert "done" in ops

    def test_bubble_empty(self):
        """空数组也能模拟。"""
        steps = simulate("bubble", [])
        assert len(steps) >= 1
        assert steps[0]["op"] == "init"

    def test_bubble_single_element(self):
        """单元素数组也能模拟。"""
        steps = simulate("bubble", [1])
        self._check_steps(steps)
        assert steps[-1]["op"] == "done"

    # ── 选择排序 ──

    def test_select_simulates(self):
        """选择排序模拟。"""
        steps = simulate("select", [5, 3, 1, 2, 4])
        self._check_steps(steps)
        self._check_final_sorted(steps, [5, 3, 1, 2, 4])

    # ── 插入排序 ──

    def test_insert_simulates(self):
        """插入排序模拟。"""
        steps = simulate("insert", [5, 3, 1, 2, 4])
        self._check_steps(steps)
        self._check_final_sorted(steps, [5, 3, 1, 2, 4])

    # ── 快速排序 ──

    def test_quick_simulates(self):
        """快速排序模拟。"""
        steps = simulate("quick", [5, 3, 1, 2, 4])
        self._check_steps(steps)
        self._check_final_sorted(steps, [5, 3, 1, 2, 4])

    # ── 归并排序 ──

    def test_merge_simulates(self):
        """归并排序模拟。"""
        steps = simulate("merge", [5, 3, 1, 2, 4])
        self._check_steps(steps)
        self._check_final_sorted(steps, [5, 3, 1, 2, 4])

    # ── 堆排序 ──

    def test_heap_simulates(self):
        """堆排序模拟。"""
        steps = simulate("heap", [5, 3, 1, 2, 4])
        self._check_steps(steps)
        self._check_final_sorted(steps, [5, 3, 1, 2, 4])

    # ── 边界 ──

    def test_unknown_algo_returns_empty(self):
        """未知算法返回空列表。"""
        steps = simulate("unknown_algo", [1, 2, 3])
        assert steps == []

    def test_already_sorted_array(self):
        """已排序数组也能正确模拟。"""
        for algo in ["bubble", "select", "insert", "quick", "merge", "heap"]:
            steps = simulate(algo, [1, 2, 3, 4, 5])
            self._check_final_sorted(steps, [1, 2, 3, 4, 5])

    def test_reverse_sorted_array(self):
        """逆序数组也能正确模拟。"""
        for algo in ["bubble", "select", "insert", "quick", "merge", "heap"]:
            steps = simulate(algo, [5, 4, 3, 2, 1])
            self._check_final_sorted(steps, [5, 4, 3, 2, 1])

    def test_duplicate_values(self):
        """含重复值的数组也能正确模拟。"""
        for algo in ["bubble", "select", "insert", "quick", "merge", "heap"]:
            steps = simulate(algo, [3, 1, 3, 2, 1])
            self._check_final_sorted(steps, [3, 1, 3, 2, 1])