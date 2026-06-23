"""测试步骤采集器。"""
from app.core.step_collector import collect_steps


class TestStepCollector:
    """步骤采集测试。"""

    def test_collects_steps_bubble(self):
        """冒泡排序：应采集到多个步骤。"""
        code = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''
        steps = collect_steps(code, [3, 1, 2])
        assert len(steps) > 1, f"Expected >1 steps, got {len(steps)}"
        # 首步初始快照
        assert steps[0]["op"] == "init"
        assert steps[0]["array_state"] == [3, 1, 2]

    def test_final_step_is_done(self):
        """正确排序后最后一步应为 done。"""
        code = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''
        steps = collect_steps(code, [3, 1, 2])
        last = steps[-1]
        assert last["op"] in ("done", "error")

    def test_empty_input(self):
        """空数组。"""
        code = '''
def sort(arr):
    return arr
'''
        steps = collect_steps(code, [])
        assert len(steps) >= 1
        assert steps[0]["array_state"] == []

    def test_syntax_error_code(self):
        """语法错误的代码。"""
        code = "def sort(:\n    pass"
        steps = collect_steps(code, [1, 2])
        assert len(steps) >= 1
        # 应有 error 步骤
        assert any(s["op"] == "error" for s in steps)

    def test_max_steps_limit(self):
        """步骤数应受 max_steps 限制。"""
        code = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''
        steps = collect_steps(code, [3, 1, 2], max_steps=10)
        assert len(steps) <= 11  # max_steps + init 步
