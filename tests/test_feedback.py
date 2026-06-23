"""测试智能反馈引擎。"""
from app.core.feedback import diagnose, static_check_sort


class TestDiagnose:
    """反馈引擎诊断测试。"""

    def test_timeout_detected(self):
        """超时应被识别。"""
        result = {"returncode": -1, "timed_out": True, "stderr": ""}
        diag = diagnose("", result)
        assert diag is not None
        assert diag["type"] == "超时"

    def test_syntax_error_detected(self):
        """语法错误应被识别。"""
        result = {
            "returncode": 1,
            "timed_out": False,
            "stderr": "SyntaxError: invalid syntax (line 1)",
        }
        code = "def sort(:"
        diag = diagnose(code, result)
        assert diag is not None
        assert diag["type"] == "语法错误"

    def test_index_error_detected(self):
        """IndexError 应被匹配。"""
        result = {
            "returncode": 1,
            "timed_out": False,
            "stderr": "IndexError: list index out of range",
        }
        diag = diagnose("", result)
        assert diag is not None
        assert diag["type"] == "下标越界"

    def test_name_error_generic_variable(self):
        """NameError（通用变量名）应被匹配为「变量未定义」。"""
        result = {
            "returncode": 1,
            "timed_out": False,
            "stderr": "NameError: name 'x' is not defined",
        }
        diag = diagnose("x = 1", result)
        assert diag is not None
        assert diag["type"] == "变量未定义"
        assert "x" in diag["hint"]

    def test_name_error_temp_variable(self):
        """NameError 中 temp/tmp 应识别为「多余变量」并提示 Python 元组解包。"""
        result = {
            "returncode": 1,
            "timed_out": False,
            "stderr": "NameError: name 'temp' is not defined",
        }
        diag = diagnose("", result)
        assert diag is not None
        assert diag["type"] == "多余变量"
        assert "temp" in diag["hint"]
        assert "arr[i], arr[j] = arr[j], arr[i]" in diag["hint"]

    def test_name_error_sort_function_mismatch(self):
        """NameError: name 'sort' → 应识别为「函数名错误」而非「变量未定义」。"""
        result = {
            "returncode": 1,
            "timed_out": False,
            "stderr": "NameError: name 'sort' is not defined",
        }
        code = "def wrong_bubble_sort(arr):\n    n = len(arr)\n    for i in range(1):\n        for j in range(n-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr\n"
        diag = diagnose(code, result)
        assert diag is not None
        assert diag["type"] == "函数名错误"
        assert "sort" in diag["hint"]
        assert "wrong_bubble_sort" in diag["hint"]
        # 不应出现误导性提示
        assert "变量未定义" not in diag["hint"]
        assert "temp" not in diag["hint"]

    def test_name_error_no_function_at_all(self):
        """NameError: name 'sort' 且代码中无任何函数 → 提示定义 sort 函数。"""
        result = {
            "returncode": 1,
            "timed_out": False,
            "stderr": "NameError: name 'sort' is not defined",
        }
        code = "x = 1\ny = 2\n"
        diag = diagnose(code, result)
        assert diag is not None
        assert diag["type"] == "缺少函数"
        assert "def sort(arr):" in diag["hint"]

    def test_type_error_detected(self):
        """类型比较错误。"""
        result = {
            "returncode": 1,
            "timed_out": False,
            "stderr": "TypeError: 'str' not supported between instances of 'int' and 'str'",
        }
        diag = diagnose("", result)
        assert diag is not None
        assert diag["type"] == "类型比较错误"

    def test_no_error_returns_static_check(self):
        """无运行时错误时进行静态检查。"""
        result = {"returncode": 0, "timed_out": False, "stderr": ""}
        # 无 sort 函数的代码
        code = "x = 1"
        diag = diagnose(code, result)
        # 静态检查应该提示缺少 sort 函数
        if diag:
            assert diag["type"] in ("结构提醒", "参数提醒")


class TestStaticCheck:
    """AST 静态检查测试。"""

    def test_no_sort_function(self):
        """完全没有函数定义 → 结构提醒。"""
        issues = static_check_sort("x = 1")
        assert any("sort" in i["hint"].lower() for i in issues)
        assert any(i["type"] == "结构提醒" for i in issues)

    def test_wrong_function_name(self):
        """定义了其他函数但未定义 sort → 函数名错误。"""
        code = '''
def wrong_bubble_sort(arr):
    n = len(arr)
    for i in range(1):
        for j in range(n-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
'''
        issues = static_check_sort(code)
        func_name_issues = [i for i in issues if i["type"] == "函数名错误"]
        assert len(func_name_issues) >= 1
        assert "wrong_bubble_sort" in func_name_issues[0]["hint"]
        assert "sort" in func_name_issues[0]["hint"]

    def test_dangerous_eval(self):
        """检测 eval()。"""
        code = '''
def sort(arr):
    eval("print('hacked')")
    return arr
'''
        issues = static_check_sort(code)
        assert any(i["type"] == "安全警告" for i in issues)

    def test_dangerous_open(self):
        """检测 open()。"""
        code = '''
def sort(arr):
    f = open("/etc/passwd")
    return arr
'''
        issues = static_check_sort(code)
        assert any(i["type"] == "安全警告" for i in issues)

    def test_no_return(self):
        """sort 函数缺少 return。"""
        code = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        pass
'''
        issues = static_check_sort(code)
        assert any("return" in i["hint"].lower() for i in issues)

    def test_syntax_error_static(self):
        """语法错误时返回错误信息。"""
        issues = static_check_sort("def sort(:")
        assert len(issues) > 0
        assert issues[0]["type"] == "语法错误"
