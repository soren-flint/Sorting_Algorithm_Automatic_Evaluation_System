"""算法档案：预置 6 种排序算法的理论复杂度指标。

用于复杂度分析（Phase 6）和题目配置校验。
"""
from typing import Any

# 算法 → 理论指标映射
ALGO_PROFILES: dict[str, dict[str, Any]] = {
    "bubble": {
        "name": "冒泡排序",
        "best": "O(n)",
        "average": "O(n²)",
        "worst": "O(n²)",
        "space": "O(1)",
        "stable": True,
        "description": "相邻元素两两比较，大的往后冒。简单但慢。",
    },
    "select": {
        "name": "选择排序",
        "best": "O(n²)",
        "average": "O(n²)",
        "worst": "O(n²)",
        "space": "O(1)",
        "stable": False,
        "description": "每轮找最小值放到前面。比较次数固定，交换次数少。",
    },
    "insert": {
        "name": "插入排序",
        "best": "O(n)",
        "average": "O(n²)",
        "worst": "O(n²)",
        "space": "O(1)",
        "stable": True,
        "description": "将元素插入已排序部分的正确位置。小规模或近似有序时很快。",
    },
    "quick": {
        "name": "快速排序",
        "best": "O(n log n)",
        "average": "O(n log n)",
        "worst": "O(n²)",
        "space": "O(log n)",
        "stable": False,
        "description": "分治策略，选 pivot 分区递归。平均最快，但最坏 O(n²)。",
    },
    "merge": {
        "name": "归并排序",
        "best": "O(n log n)",
        "average": "O(n log n)",
        "worst": "O(n log n)",
        "space": "O(n)",
        "stable": True,
        "description": "分治递归，两路归并。稳定且 O(n log n)，但需额外空间。",
    },
    "heap": {
        "name": "堆排序",
        "best": "O(n log n)",
        "average": "O(n log n)",
        "worst": "O(n log n)",
        "space": "O(1)",
        "stable": False,
        "description": "建堆 + 反复弹出堆顶。O(n log n) 原地排序，但不稳定。",
    },
}


def get_profile(algo_type: str) -> dict[str, Any] | None:
    """获取算法的理论指标。

    Args:
        algo_type: 算法标识，如 "bubble"、"quick"。

    Returns:
        dict | None: 算法档案，未找到返回 None。
    """
    # 兼容带中文后缀的识别结果
    key = algo_type.split("(")[0].strip().lower() if "(" in algo_type else algo_type.strip().lower()
    return ALGO_PROFILES.get(key)


def check_ceiling(estimated_complexity: str, ceiling: str | None) -> dict:
    """检查估算复杂度是否达到题目门槛。

    Args:
        estimated_complexity: 实测估算结果，如 "O(n²)"。
        ceiling: 题目复杂度门槛，如 "O(n log n)"，None 表示不设限。

    Returns:
        dict: {"meets": bool, "message": str}
    """
    if ceiling is None:
        return {"meets": True, "message": "本题未设复杂度门槛"}

    # 复杂度等级（数字越大越慢）
    RANKS = {"O(1)": 0, "O(log n)": 1, "O(n)": 2, "O(n log n)": 3,
             "O(n²)": 4, "O(n³)": 5, "O(2ⁿ)": 6}

    est_rank = RANKS.get(estimated_complexity, 99)
    ceil_rank = RANKS.get(ceiling, 99)

    if est_rank <= ceil_rank:
        return {"meets": True, "message": f"估算 {estimated_complexity} ≤ 门槛 {ceiling}，满足要求"}
    else:
        return {"meets": False,
                "message": f"估算 {estimated_complexity} 超过门槛 {ceiling}——答案正确但解法不够优"}