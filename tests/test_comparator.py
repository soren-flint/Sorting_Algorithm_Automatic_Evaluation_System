"""测试输出比对器。"""
from app.core.comparator import compare_outputs


class TestComparator:
    """输出比对测试。"""

    def test_exact_match(self):
        """输出与期望完全一致。"""
        result = compare_outputs("[1,2,3]", "[1,2,3]", [3, 1, 2], "strict")
        assert result["passed"] is True
        assert result["actual_parsed"] == [1, 2, 3]

    def test_mismatch(self):
        """输出与期望不一致。"""
        result = compare_outputs("[3,2,1]", "[1,2,3]", [3, 2, 1], "strict")
        assert result["passed"] is False
        assert result["diff"] is not None

    def test_invalid_json_output(self):
        """无法解析的输出。"""
        result = compare_outputs("not json", "[1,2,3]", [1, 2, 3], "strict")
        assert result["passed"] is False
        assert "解析" in result["reason"]

    def test_not_list_output(self):
        """输出不是数组。"""
        result = compare_outputs('{"a":1}', "[1,2,3]", [1, 2, 3], "strict")
        assert result["passed"] is False
        assert "数组" in result["reason"]

    def test_no_expected_uses_validator(self):
        """无期望输出时走 validator 判定。"""
        result = compare_outputs("[1,2,3]", None, [3, 1, 2], "strict")
        assert result["passed"] is True

    def test_stalin_without_expected(self):
        """斯大林模式无期望输出。"""
        result = compare_outputs("[1,3,5]", None, [1, 3, 2, 5, 4], "stalin")
        assert result["passed"] is True
