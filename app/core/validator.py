"""排序定义判定器。

支持的排序规则：
- strict:  标准排序——输出必须有序且是输入的排列（元素不增不减）
- stalin:  斯大林排序——允许删元素，剩余序列必须有序且是输入的子序列
- stable:  稳定排序——有序+排列，相同元素相对顺序不变
- topk:    Top-K 排序——前 K 个有序即可（K 由题目配置）

核心判定函数全部是纯函数，不依赖 Flask/SQLAlchemy。
"""
from collections import Counter


def is_monotonic(arr: list) -> bool:
    """检查数组是否非递减有序。

    Args:
        arr: 待检查列表。

    Returns:
        bool: 是否有序（含空数组和单元素数组，视为有序）。
    """
    if len(arr) <= 1:
        return True
    return all(arr[i] <= arr[i + 1] for i in range(len(arr) - 1))


def is_permutation(a: list, b: list) -> bool:
    """检查两个数组是否互为排列（multiset 相同）。

    使用 Counter 比 sorted() == sorted() 更严谨：
    - 时间复杂度 O(n)，而非 O(n log n)
    - 正确处理非可比元素

    Args:
        a, b: 两个列表。

    Returns:
        bool: 元素构成是否完全相同。
    """
    return Counter(a) == Counter(b)


def is_subsequence(short: list, long: list) -> bool:
    """检查 short 是否是 long 的子序列（保持相对顺序）。

    用于斯大林排序判定：删除部分元素后，剩余序列必须是原序列的子序列。

    Args:
        short: 较短的序列（学生输出）。
        long: 较长的序列（原始输入）。

    Returns:
        bool: short 是否为 long 的子序列。
    """
    it = iter(long)
    return all(x in it for x in short)


def validate_sort(output: list, input_arr: list, rule: str = "strict",
                  k: int | None = None) -> dict:
    """按指定规则判定排序正确性。

    Args:
        output: 学生代码的输出数组。
        input_arr: 原始输入数组。
        rule: 排序规则，可选 strict/stalin/stable/topk。
        k: Top-K 规则的 K 值（仅 rule=topk 时使用）。

    Returns:
        dict: {"passed": bool, "reason": str}
    """
    # 输入类型校验
    if not isinstance(output, list) or not isinstance(input_arr, list):
        return {"passed": False,
                "reason": "输入类型错误：output 和 input_arr 必须为 list"}

    if rule == "strict":
        if not is_monotonic(output):
            return {
                "passed": False,
                "reason": "输出未完全有序（存在逆序对——某个位置的元素比它后面的元素大）",
            }
        if not is_permutation(output, input_arr):
            return {
                "passed": False,
                "reason": "输出不是输入的排列（元素被增减了——排序不应该改变元素构成）",
            }
        return {"passed": True, "reason": "通过：有序且是输入的排列"}

    if rule == "stalin":
        if not is_monotonic(output):
            return {
                "passed": False,
                "reason": "剩余序列未有序——斯大林排序要求删除后留下的序列必须升序",
            }
        if not is_subsequence(output, input_arr):
            return {
                "passed": False,
                "reason": "输出不是输入的子序列——斯大林排序只能删除元素，不能新增或改变顺序",
            }
        return {"passed": True, "reason": "通过：剩余有序且是输入的子序列（斯大林排序正确）"}

    if rule == "stable":
        if not is_monotonic(output):
            return {"passed": False, "reason": "输出未有序"}
        if not is_permutation(output, input_arr):
            return {"passed": False, "reason": "输出不是输入的排列"}
        # 稳定性检测需要原始下标，通过步骤采集验证
        # 这里只做基础判定
        return {"passed": True, "reason": "通过（稳定性需可视化/步骤采集核验）"}

    if rule == "topk":
        if k is None:
            return {"passed": False, "reason": "Top-K 规则未配置 K 值"}
        # 前 K 个必须有序
        if not is_monotonic(output[:k]):
            return {"passed": False,
                    "reason": f"前 {k} 个元素未有序（Top-{k} 要求前 {k} 个升序）"}
        # 整体必须是输入的排列
        if not is_permutation(output, input_arr):
            return {"passed": False, "reason": "输出不是输入的排列"}
        return {"passed": True, "reason": f"通过：前 {k} 个有序，整体是排列"}

    return {"passed": False, "reason": f"未知的排序规则: {rule}"}


def check_off_by_one(output: list, expected: list) -> str | None:
    """检测常见的 off-by-one 错误。

    比较学生输出与期望输出，尝试诊断是否差一个元素。

    Args:
        output: 学生输出。
        expected: 期望输出。

    Returns:
        str | None: 诊断提示，无问题返回 None。
    """
    if len(output) == len(expected) + 1:
        return "输出比期望多一个元素——检查循环边界，是否多跑了一轮？"
    if len(output) == len(expected) - 1:
        return "输出比期望少一个元素——检查循环边界，是否少跑了一轮？"
    if len(output) == len(expected):
        # 长度相同但内容不同——检查是否是交换方向反了
        if sorted(output) == sorted(expected) and output != expected:
            if output == list(reversed(expected)):
                return "输出是完全逆序——比较方向可能写反了（> 写成 < 或反之）"
    return None