"""复杂度估算器：多规模实测反推时间复杂度。

方法：用 n=100/500/1000/2000 四组逆序数据实测学生代码耗时，
通过相邻规模耗时比值反推复杂度：
  - 比值 < 2.5 → O(n)
  - 比值 2.5~3.5 → O(n log n)
  - 比值 > 3.5 → O(n²)

按需触发，不在常规评测链路中（避免拖慢提交速度）。
"""
import json
import time

from app.core.sandbox import run_code


# 模板使用 %s 占位符，避免用户代码中的 {} 花括号被 f-string 误解析
_COMPLEXITY_WRAPPER_HEAD = '''\
import json, sys

'''

_COMPLEXITY_WRAPPER_TAIL = '''


if __name__ == "__main__":
    input_data = json.loads(sys.stdin.read())
    t0 = __import__("time").perf_counter()
    result = sort(input_data)
    t1 = __import__("time").perf_counter()
    print(json.dumps({"result": result, "elapsed": round(t1 - t0, 6)}))
'''


def _wrap_code(user_code: str) -> str:
    """将学生代码包装为可执行的完整脚本（使用拼接，避免 f-string 注入）。"""
    return _COMPLEXITY_WRAPPER_HEAD + user_code + _COMPLEXITY_WRAPPER_TAIL


def estimate(user_code: str, sizes: list[int] | None = None,
             timeout: float = 15.0) -> dict:
    """多规模实测反推复杂度。

    Args:
        user_code: 学生排序代码（含 sort 函数定义）。
        sizes: 测试规模列表，默认 [100, 500, 1000, 2000]。
        timeout: 每次执行的超时秒数。

    Returns:
        dict: {
            "estimated": str,      估算结果，如 "O(n²)"
            "timings": dict,       各规模耗时 {100: 0.012, 500: 0.15, ...}
            "ratios": list[float], 相邻规模耗时比
            "success": bool,       是否成功完成所有测试
            "error": str | None,
        }
    """
    if sizes is None:
        sizes = [100, 500, 1000, 2000]

    wrapped = _wrap_code(user_code)
    timings: dict[int, float] = {}

    for size in sizes:
        # 生成逆序输入 [size, size-1, ..., 1]
        input_arr = list(range(size, 0, -1))
        stdin = json.dumps(input_arr)

        result = run_code(wrapped, stdin, timeout=timeout)

        if result["timed_out"]:
            return {
                "estimated": "超时",
                "timings": {str(k): v for k, v in timings.items()},
                "ratios": [],
                "success": False,
                "error": f"n={size} 时超时",
            }
        if result["returncode"] != 0:
            return {
                "estimated": "错误",
                "timings": {str(k): v for k, v in timings.items()},
                "ratios": [],
                "success": False,
                "error": result["stderr"][-200:],
            }

        try:
            output = json.loads(result["stdout"])
            elapsed = output.get("elapsed", 0.0)
        except (json.JSONDecodeError, KeyError):
            elapsed = 0.0

        timings[size] = elapsed

    # 计算相邻规模耗时比
    sorted_sizes = sorted(timings.keys())
    ratios = []
    for k in range(1, len(sorted_sizes)):
        prev = timings[sorted_sizes[k - 1]]
        curr = timings[sorted_sizes[k]]
        if prev > 0:
            ratios.append(round(curr / prev, 2))
        else:
            ratios.append(0.0)

    # 取最大比值判断复杂度
    max_ratio = max(ratios) if ratios else 0

    if max_ratio < 2.5:
        estimated = "O(n)"
    elif max_ratio < 3.5:
        estimated = "O(n log n)"
    else:
        estimated = "O(n²)"

    return {
        "estimated": estimated,
        "timings": {str(k): v for k, v in timings.items()},
        "ratios": ratios,
        "success": True,
        "error": None,
        "max_ratio": max_ratio,
    }
