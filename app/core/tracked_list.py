"""TrackedList：拦截 list 变更操作，记录每步数组快照。

供 sandbox（run_code_with_collect）和 step_collector（_collect_tracked）共享使用，
避免两处独立定义导致行为不一致。
"""


class TrackedList(list):
    """list 子类，拦截 __setitem__ / pop / append 并记录操作快照。

    快照格式: {seq, array_state, op, i, j, note}，与渲染层协议一致。
    """

    _truncated_warned: bool = False  # 类级标志，避免重复警告

    def __init__(self, iterable, steps: list, max_steps: int = 500):
        """初始化 TrackedList。

        Args:
            iterable: 初始数据。
            steps: 外部步骤列表（会被原地修改）。
            max_steps: 最大步骤数，超过后截断并警告一次。
        """
        super().__init__(iterable)
        self._steps = steps
        self._max_steps = max_steps

    def _record(self, op: str, i=None, j=None, note: str = ""):
        """记录一次操作快照。"""
        if len(self._steps) < self._max_steps:
            self._steps.append({
                "seq": len(self._steps),
                "array_state": list(self),
                "op": op,
                "i": i,
                "j": j,
                "note": note,
            })
        elif not TrackedList._truncated_warned:
            TrackedList._truncated_warned = True
            self._steps.append({
                "seq": len(self._steps),
                "array_state": list(self),
                "op": "warning",
                "i": None,
                "j": None,
                "note": f"步骤已达上限 {self._max_steps}，后续步骤被截断",
            })

    # ── 拦截方法 ──

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        idx = key if isinstance(key, int) else None
        self._record("set", i=idx, note=f"arr[{key}] = {value}")

    def pop(self, *args):
        if len(self) == 0:
            self._record("delete", i=None, note="pop from empty list")
            raise IndexError("pop from empty list")
        idx = args[0] if args else len(self) - 1
        old = super().pop(*args)
        self._record("delete", i=idx,
                     note=f"pop({args[0] if args else ''}) → {old}")
        return old

    def append(self, value):
        super().append(value)
        self._record("set", i=len(self) - 1, note=f"append({value})")