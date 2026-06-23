"""测试沙箱执行器。"""
import json

from app.core.sandbox import run_code


class TestSandbox:
    """沙箱基础功能测试。"""

    def test_run_bubble_sort(self):
        """正确冒泡排序：应返回有序结果。"""
        code = '''
import json, sys
def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

input_data = json.loads(sys.stdin.read())
result = sort(input_data)
print(json.dumps(result))
'''
        result = run_code(code, "[5,2,8,1,3]")
        assert result["returncode"] == 0
        assert not result["timed_out"]
        parsed = json.loads(result["stdout"])
        assert parsed == [1, 2, 3, 5, 8]

    def test_empty_array(self):
        """空数组输入。"""
        code = '''
import json, sys
input_data = json.loads(sys.stdin.read())
print(json.dumps(input_data))
'''
        result = run_code(code, "[]")
        assert result["returncode"] == 0
        assert json.loads(result["stdout"]) == []

    def test_single_element(self):
        """单元素数组。"""
        code = '''
import json, sys
input_data = json.loads(sys.stdin.read())
print(json.dumps(input_data))
'''
        result = run_code(code, "[1]")
        assert result["returncode"] == 0
        assert json.loads(result["stdout"]) == [1]

    def test_syntax_error(self):
        """语法错误代码。"""
        code = "def sort(:"
        result = run_code(code, "[1,2]")
        assert result["returncode"] != 0
        assert "SyntaxError" in result["stderr"] or result["returncode"] == 1

    def test_runtime_error(self):
        """运行时错误（未定义变量）。"""
        code = '''
import json, sys
x = undefined_var
'''
        result = run_code(code, "")
        assert result["returncode"] != 0
        assert "NameError" in result["stderr"]

    def test_timeout(self):
        """死循环应在 timeout 内被终止。"""
        code = "while True:\n    pass"
        result = run_code(code, "", timeout=1.0)
        assert result["timed_out"] is True
        assert result["returncode"] == -1

    def test_no_input(self):
        """不需要 stdin 的代码。"""
        code = "print('hello')"
        result = run_code(code, "")
        assert result["returncode"] == 0
        assert "hello" in result["stdout"]
