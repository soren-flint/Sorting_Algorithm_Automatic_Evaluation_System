"""算法模拟器：用 Python 生成器模拟 6 种排序算法，产出可视化步骤。

每个模拟器函数接收输入数组，yield 步骤 dict。
步骤格式与 JS 端 ALGO_GENERATORS 一致，与 SortStep 模型兼容。

步骤 dict 结构:
    {
        "seq": int,           # 步骤序号（调用方负责编号）
        "array_state": list,  # 数组快照
        "op": str,            # init|compare|swap|set|done
        "i": int|None,        # 操作下标 i
        "j": int|None,        # 操作下标 j
        "note": str,          # 操作说明
        "round": int,         # 当前轮次（外层循环）
    }
"""
from typing import Iterator


def simulate(algo: str, arr: list) -> list[dict]:
    """模拟指定算法，返回完整步骤列表。

    Args:
        algo: 算法类型（bubble|select|insert|quick|merge|heap）。
        arr: 输入数组（会被复制，不修改原数组）。

    Returns:
        list[dict]: 步骤列表，已编号 seq。
    """
    simulators = {
        "bubble": _simulate_bubble,
        "select": _simulate_select,
        "insert": _simulate_insert,
        "quick": _simulate_quick,
        "merge": _simulate_merge,
        "heap": _simulate_heap,
        "stalin": _simulate_stalin,
        "merciful_stalin": _simulate_merciful_stalin,
        "sleep": _simulate_sleep,
        "iterative": _simulate_stalin,  # 未明确识别时回退到斯大林模拟
    }
    sim_fn = simulators.get(algo)
    if sim_fn is None:
        return []

    steps = list(sim_fn(list(arr)))
    # 统一编号
    for idx, step in enumerate(steps):
        step["seq"] = idx
    return steps


# ── 辅助 ────────────────────────────────────────────────

def _make_step(arr: list, op: str, i=None, j=None, note: str = "",
               round_num: int = 0) -> dict:
    """创建单步 dict（seq 由调用方填充）。"""
    return {
        "seq": 0,
        "array_state": list(arr),
        "op": op,
        "i": i,
        "j": j,
        "note": note,
        "round": round_num,
    }


# ── 冒泡排序 ────────────────────────────────────────────

def _simulate_bubble(arr: list) -> Iterator[dict]:
    n = len(arr)
    yield _make_step(arr, "init", note="初始状态：数组包含 {} 个元素，全部未排序。".format(n))

    for i in range(n - 1):
        r = i + 1
        yield _make_step(arr, "compare", note=f"🔄 第 {r} 轮开始", round_num=r)
        for j in range(n - 1 - i):
            yield _make_step(arr, "compare", i=j, j=j + 1,
                             note=f"🔍 比较 arr[{j}]={arr[j]} 与 arr[{j+1}]={arr[j+1]}",
                             round_num=r)
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                yield _make_step(arr, "swap", i=j, j=j + 1,
                                 note=f"🔀 交换 arr[{j}] 与 arr[{j+1}]",
                                 round_num=r)
            else:
                yield _make_step(arr, "compare", i=j, j=j + 1,
                                 note="✓ 无需交换", round_num=r)
        yield _make_step(arr, "set",
                         note=f"🏁 第 {r} 轮结束：arr[{n - i - 1}]={arr[n - i - 1]} 已就位",
                         round_num=r)

    yield _make_step(arr, "done", note="🎉 排序完成！")


# ── 选择排序 ────────────────────────────────────────────

def _simulate_select(arr: list) -> Iterator[dict]:
    n = len(arr)
    yield _make_step(arr, "init", note=f"初始状态：数组包含 {n} 个元素。")

    for i in range(n - 1):
        r = i + 1
        min_idx = i
        yield _make_step(arr, "compare", i=i, note=f"🔄 第 {r} 轮：设 min_idx = {i}", round_num=r)
        for j in range(i + 1, n):
            yield _make_step(arr, "compare", i=min_idx, j=j,
                             note=f"🔍 比较 arr[{min_idx}]={arr[min_idx]} 与 arr[{j}]={arr[j]}",
                             round_num=r)
            if arr[j] < arr[min_idx]:
                min_idx = j
        if min_idx != i:
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
            yield _make_step(arr, "swap", i=i, j=min_idx,
                             note=f"🔀 将最小值 arr[{i}]={arr[i]} 交换到位置 {i}",
                             round_num=r)
        else:
            yield _make_step(arr, "set", i=i,
                             note=f"✓ arr[{i}] 已在正确位置",
                             round_num=r)

    yield _make_step(arr, "done", note="🎉 排序完成！")


# ── 插入排序 ────────────────────────────────────────────

def _simulate_insert(arr: list) -> Iterator[dict]:
    n = len(arr)
    yield _make_step(arr, "init", note=f"初始状态：数组包含 {n} 个元素。")

    for i in range(1, n):
        r = i
        key = arr[i]
        j = i - 1
        yield _make_step(arr, "compare", i=i, note=f"🔄 第 {r} 轮：取出 key = arr[{i}] = {key}",
                         round_num=r)
        while j >= 0 and arr[j] > key:
            yield _make_step(arr, "compare", i=j, j=j + 1,
                             note=f"🔍 比较 arr[{j}]={arr[j]} 与 key={key} → 需要后移",
                             round_num=r)
            arr[j + 1] = arr[j]
            yield _make_step(arr, "set", i=j + 1,
                             note=f"📝 arr[{j + 1}] = arr[{j}] = {arr[j]}",
                             round_num=r)
            j -= 1
        if j >= 0:
            yield _make_step(arr, "compare", i=j, j=j + 1,
                             note=f"🔍 arr[{j}]={arr[j]} ≤ key={key} → 停止",
                             round_num=r)
        arr[j + 1] = key
        yield _make_step(arr, "set", i=j + 1,
                         note=f"📝 arr[{j + 1}] = key = {key}",
                         round_num=r)

    yield _make_step(arr, "done", note="🎉 排序完成！")


# ── 快速排序 ────────────────────────────────────────────

def _simulate_quick(arr: list) -> Iterator[dict]:
    yield _make_step(arr, "init", note="初始状态：快速排序开始（递归分区）。")

    def _qs(a: list, lo: int, hi: int, round_base: int) -> Iterator[dict]:
        if lo >= hi:
            return
        pivot = a[hi]
        i = lo - 1
        for j in range(lo, hi):
            yield _make_step(a, "compare", i=j, j=hi,
                             note=f"🔍 比较 arr[{j}]={a[j]} 与 pivot arr[{hi}]={pivot}",
                             round_num=round_base + j)
            if a[j] <= pivot:
                i += 1
                if i != j:
                    a[i], a[j] = a[j], a[i]
                    yield _make_step(a, "swap", i=i, j=j,
                                     note=f"🔀 交换 arr[{i}] ↔ arr[{j}]",
                                     round_num=round_base + j)
        a[i + 1], a[hi] = a[hi], a[i + 1]
        yield _make_step(a, "swap", i=i + 1, j=hi,
                         note=f"📌 将 pivot={pivot} 放到正确位置 arr[{i + 1}]",
                         round_num=round_base + hi)
        yield from _qs(a, lo, i, round_base + 100)
        yield from _qs(a, i + 2, hi, round_base + 200)

    yield from _qs(arr, 0, len(arr) - 1, 0)
    yield _make_step(arr, "done", note="🎉 排序完成！")


# ── 归并排序 ────────────────────────────────────────────

def _simulate_merge(arr: list) -> Iterator[dict]:
    yield _make_step(arr, "init", note="初始状态：归并排序开始（分解 + 合并）。")

    def _ms(a: list, lo: int, hi: int, depth: int) -> Iterator[dict]:
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        yield from _ms(a, lo, mid, depth + 1)
        yield from _ms(a, mid + 1, hi, depth + 1)

        # merge in-place (visualization via temp arrays)
        left = a[lo:mid + 1]
        right = a[mid + 1:hi + 1]
        k = lo
        li = 0
        ri = 0
        while li < len(left) and ri < len(right):
            # 构造修正后的数组副本：a[lo+li] / a[mid+1+ri] 可能已被
            # 之前的合并写覆盖，所以恢复为 left[li] / right[ri]
            arr_copy = list(a)
            if lo + li < len(arr_copy):
                arr_copy[lo + li] = left[li]
            if mid + 1 + ri < len(arr_copy):
                arr_copy[mid + 1 + ri] = right[ri]
            yield _make_step(arr_copy, "compare", i=lo + li, j=mid + 1 + ri,
                             note=f"🔍 比较 left[{li}]={left[li]} 与 right[{ri}]={right[ri]}",
                             round_num=depth)
            if left[li] <= right[ri]:
                a[k] = left[li]
                yield _make_step(a, "set", i=k,
                                 note=f"📝 arr[{k}] = left[{li}] = {left[li]}",
                                 round_num=depth)
                li += 1
            else:
                a[k] = right[ri]
                yield _make_step(a, "set", i=k,
                                 note=f"📝 arr[{k}] = right[{ri}] = {right[ri]}",
                                 round_num=depth)
                ri += 1
            k += 1
        while li < len(left):
            a[k] = left[li]
            yield _make_step(a, "set", i=k,
                             note=f"📝 arr[{k}] = left[{li}] = {left[li]}",
                             round_num=depth)
            li += 1
            k += 1
        while ri < len(right):
            a[k] = right[ri]
            yield _make_step(a, "set", i=k,
                             note=f"📝 arr[{k}] = right[{ri}] = {right[ri]}",
                             round_num=depth)
            ri += 1
            k += 1

    yield from _ms(arr, 0, len(arr) - 1, 0)
    yield _make_step(arr, "done", note="🎉 排序完成！")


# ── 堆排序 ──────────────────────────────────────────────

def _simulate_heap(arr: list) -> Iterator[dict]:
    n = len(arr)
    yield _make_step(arr, "init", note="初始状态：堆排序开始（建堆 + 排序）。")

    def _heapify(a: list, size: int, root: int, depth: int) -> Iterator[dict]:
        largest = root
        left = 2 * root + 1
        right = 2 * root + 2
        if left < size:
            yield _make_step(a, "compare", i=largest, j=left,
                             note=f"🔍 比较 arr[{largest}]={a[largest]} 与 arr[{left}]={a[left]}",
                             round_num=depth)
            if a[left] > a[largest]:
                largest = left
        if right < size:
            yield _make_step(a, "compare", i=largest, j=right,
                             note=f"🔍 比较 arr[{largest}]={a[largest]} 与 arr[{right}]={a[right]}",
                             round_num=depth)
            if a[right] > a[largest]:
                largest = right
        if largest != root:
            a[root], a[largest] = a[largest], a[root]
            yield _make_step(a, "swap", i=root, j=largest,
                             note=f"🔀 交换 arr[{root}] ↔ arr[{largest}]",
                             round_num=depth)
            yield from _heapify(a, size, largest, depth + 1)

    # 建堆
    for i in range(n // 2 - 1, -1, -1):
        yield from _heapify(arr, n, i, 0)

    # 排序
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        yield _make_step(arr, "swap", i=0, j=i,
                         note=f"🔀 将堆顶 arr[0]={arr[i]} 放到位置 {i}",
                         round_num=n - i)
        yield from _heapify(arr, i, 0, n - i + 1)

    yield _make_step(arr, "done", note="🎉 排序完成！")


# ── 斯大林排序（Stalin Sort）──────────────────────────────

def _simulate_stalin(arr: list) -> Iterator[dict]:
    """斯大林排序模拟：单遍扫描，保留升序元素，淘汰'不顺从'的元素。"""
    n = len(arr)
    yield _make_step(arr, "init", note=f"初始状态：斯大林排序 — 遍历数组，淘汰破坏升序的元素。共 {n} 个元素。")

    if n == 0:
        yield _make_step(arr, "done", note="🎉 空数组，排序完成！")
        return

    # 结果列表（模拟原地效果：在 arr 副本上逐步构建）
    result = [arr[0]]
    working = list(arr)
    yield _make_step(working, "set", i=0,
                     note=f"📌 保留 arr[0]={arr[0]} 作为起点",
                     round_num=1)

    for idx in range(1, n):
        r = idx + 1
        x = arr[idx]
        last = result[-1]
        yield _make_step(working, "compare", i=idx, j=len(result) - 1,
                         note=f"🔍 比较 arr[{idx}]={x} 与 result[-1]={last}",
                         round_num=r)
        if x >= last:
            result.append(x)
            working = list(result) + arr[len(result):]
            yield _make_step(working, "set", i=len(result) - 1,
                             note=f"✅ 保留 arr[{idx}]={x}（≥ {last}）",
                             round_num=r)
        else:
            working[idx] = None
            yield _make_step(working, "eliminate", i=idx,
                             note=f"💥 枪毙 arr[{idx}]={x}（< {last}）⛔",
                             round_num=r)

    final = list(result)
    yield _make_step(final, "done",
                     note=f"🎉 斯大林排序完成！保留 {len(result)}/{n} 个元素：{final}")


# ── 仁慈的斯大林排序（Merciful Stalin Sort）────────────────

def _simulate_merciful_stalin(arr: list) -> Iterator[dict]:
    """仁慈版斯大林排序：递归分解 + 归并，保留全部元素。"""
    n = len(arr)
    yield _make_step(arr, "init", note=f"初始状态：仁慈斯大林排序 — 递归分解 + 归并。共 {n} 个元素。")

    def _mss(a: list, depth: int = 0) -> Iterator[dict]:
        if len(a) <= 1:
            return
        kept = [a[0]]
        dropped = []
        working = list(a)
        yield _make_step(working, "set", i=0,
                         note=f"📌 第 {depth + 1} 层：保留 arr[0]={a[0]}",
                         round_num=depth)

        for idx in range(1, len(a)):
            x = a[idx]
            last = kept[-1]
            yield _make_step(working, "compare", i=idx, j=len(kept) - 1,
                             note=f"🔍 第 {depth + 1} 层：比较 arr[{idx}]={x} 与 kept[-1]={last}",
                             round_num=depth)
            if x >= last:
                kept.append(x)
                yield _make_step(working, "set", i=idx,
                                 note=f"✅ 保留 arr[{idx}]={x}",
                                 round_num=depth)
            else:
                dropped.append(x)
                yield _make_step(working, "compare", i=idx,
                                 note=f"📦 暂存 arr[{idx}]={x} 到淘汰列表（共 {len(dropped)} 个）",
                                 round_num=depth)

        if dropped:
            yield from _mss(dropped, depth + 1)
            # 归并 kept 和 dropped（简化展示）
            merged = sorted(kept + dropped)
            yield _make_step(merged, "done",
                             note=f"🔗 第 {depth + 1} 层归并完成：{merged}",
                             round_num=depth)

    yield from _mss(list(arr), 0)
    final = sorted(arr)
    yield _make_step(final, "done", note=f"🎉 仁慈斯大林排序完成！全部 {n} 个元素正确排序：{final}")


# ── 睡眠排序（Sleep Sort）────────────────────────────────

def _simulate_sleep(arr: list) -> Iterator[dict]:
    """睡眠排序模拟：元素按其值大小依次"醒来"，从小到大加入结果。"""
    n = len(arr)
    yield _make_step(arr, "init", note=f"💤 初始状态：睡眠排序 — 全部 {n} 个元素进入睡眠，按其值倒计时。共 {n} 个元素。")

    if n == 0:
        yield _make_step(arr, "done", note="🎉 空数组，排序完成！")
        return

    # 按值升序确定"醒来"顺序
    sorted_pairs = sorted(enumerate(arr), key=lambda x: x[1])
    working = list(arr)
    # 初始：所有元素标记为"睡眠"
    yield _make_step(working, "sleep",
                     note=f"💤 全部 {n} 个元素正在睡眠中，最小值的元素将最先醒来…",
                     round_num=0)

    for rank, (orig_idx, val) in enumerate(sorted_pairs):
        r = rank + 1
        # 标记正在评估计时器
        yield _make_step(working, "compare", i=orig_idx,
                         note=f"⏳ 第 {r} 个醒来：arr[{orig_idx}]={val} 计时器归零，正在唤醒…",
                         round_num=r)
        # 元素醒来：从数组中"消失"（粒子上升），加入结果
        working[orig_idx] = None
        yield _make_step(working, "wake", i=orig_idx,
                         note=f"✨ arr[{orig_idx}]={val} 醒来！第 {r}/{n} 个元素就位",
                         round_num=r)

    final = [v for _, v in sorted_pairs]
    yield _make_step(final, "done",
                     note=f"🎉 睡眠排序完成！全部 {n} 个元素按值从小到大依次醒来：{final}")