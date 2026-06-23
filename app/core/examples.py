"""排序算法标准示例代码 — 单一定义源。

seed.py 和 grader.py 共享此模块，避免两处维护同一批示例代码。
"""
EXAMPLE_CODE: dict[str, str] = {
    "bubble": '''def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr''',
    "select": '''def sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr''',
    "insert": '''def sort(arr):
    n = len(arr)
    for i in range(1, n):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr''',
    "quick": '''def sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return sort(left) + mid + sort(right)''',
    "merge": '''def sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    L = sort(arr[:mid])
    R = sort(arr[mid:])
    result, i, j = [], 0, 0
    while i < len(L) and j < len(R):
        if L[i] <= R[j]:
            result.append(L[i]); i += 1
        else:
            result.append(R[j]); j += 1
    return result + L[i:] + R[j:]''',
    "heap": '''def sort(arr):
    def heapify(a, n, i):
        largest = i
        l, r = 2 * i + 1, 2 * i + 2
        if l < n and a[l] > a[largest]: largest = l
        if r < n and a[r] > a[largest]: largest = r
        if largest != i:
            a[i], a[largest] = a[largest], a[i]
            heapify(a, n, largest)
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1): heapify(arr, n, i)
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)
    return arr''',
    "stalin": '''def sort(arr):
    if not arr:
        return []
    result = [arr[0]]
    for x in arr[1:]:
        if x >= result[-1]:
            result.append(x)
    return result''',
    "bogo": '''import random

def sort(arr):
    """猴子排序：随机打乱直到有序（仅供娱乐）"""
    max_attempts = 500000
    for attempt in range(1, max_attempts + 1):
        ordered = True
        for i in range(len(arr) - 1):
            if arr[i] > arr[i + 1]:
                ordered = False
                break
        if ordered:
            return arr
        random.shuffle(arr)
        if attempt % 10000 == 0:
            print(f"已尝试 {attempt} 次…")
    return arr''',
    "sleep": '''import threading, time

def sort(arr):
    """睡眠排序：每个元素按其值"睡"对应秒数后输出（仅供娱乐）"""
    if not arr:
        return []
    result = []
    lock = threading.Lock()
    def worker(val):
        sleep_time = val / 10.0
        if sleep_time < 0:
            sleep_time = 0
        time.sleep(sleep_time)
        with lock:
            result.append(val)
    threads = [threading.Thread(target=worker, args=(v,)) for v in arr]
    for t in threads: t.start()
    for t in threads: t.join(timeout=30)
    return result''',
    "merciful_stalin": '''def sort(arr):
    """仁慈的斯大林排序：不直接删除，递归排序后归并"""
    if len(arr) <= 1:
        return arr[:]
    kept = [arr[0]]
    dropped = []
    for x in arr[1:]:
        if x >= kept[-1]:
            kept.append(x)
        else:
            dropped.append(x)
    if not dropped:
        return kept
    sorted_dropped = sort(dropped)
    result, i, j = [], 0, 0
    while i < len(kept) and j < len(sorted_dropped):
        if kept[i] <= sorted_dropped[j]:
            result.append(kept[i]); i += 1
        else:
            result.append(sorted_dropped[j]); j += 1
    return result + kept[i:] + sorted_dropped[j:]''',
}