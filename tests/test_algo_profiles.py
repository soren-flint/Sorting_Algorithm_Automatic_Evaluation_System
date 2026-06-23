"""测试算法档案。"""
from app.core.algo_profiles import get_profile, check_ceiling, ALGO_PROFILES


class TestAlgoProfiles:
    """算法档案查询测试。"""

    def test_all_profiles_exist(self):
        """6 种算法档案齐全。"""
        expected = {"bubble", "select", "insert", "quick", "merge", "heap"}
        assert set(ALGO_PROFILES.keys()) == expected

    def test_get_bubble_profile(self):
        profile = get_profile("bubble")
        assert profile is not None
        assert profile["name"] == "冒泡排序"
        assert profile["average"] == "O(n²)"

    def test_get_quick_profile(self):
        profile = get_profile("quick")
        assert profile is not None
        assert profile["average"] == "O(n log n)"

    def test_get_with_chinese_suffix(self):
        """带中文后缀的识别结果也能查。"""
        profile = get_profile("quick(快速排序)")
        assert profile is not None
        assert profile["name"] == "快速排序"

    def test_get_unknown(self):
        """未知算法返回 None。"""
        profile = get_profile("unknown")
        assert profile is None


class TestCheckCeiling:
    """复杂度门槛检查。"""

    def test_no_ceiling(self):
        """无门槛时始终通过。"""
        result = check_ceiling("O(n²)", None)
        assert result["meets"] is True

    def test_meets_ceiling(self):
        """O(n log n) 满足 O(n log n) 门槛。"""
        result = check_ceiling("O(n log n)", "O(n log n)")
        assert result["meets"] is True

    def test_exceeds_ceiling(self):
        """O(n²) 超过 O(n log n) 门槛。"""
        result = check_ceiling("O(n²)", "O(n log n)")
        assert result["meets"] is False
