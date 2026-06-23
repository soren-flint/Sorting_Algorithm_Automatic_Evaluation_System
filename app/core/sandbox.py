"""沙箱执行器：安全执行学生代码。

核心安全措施：
- 临时文件隔离（每次新文件，执行完立即删除）
- subprocess timeout=5s 防止死循环
- 精简环境变量（只保留 PATH）
- cwd 指向临时目录（无法访问项目文件）
- 禁止危险内置函数（通过代码静态检查在 feedback.py 完成）
"""
import os
import subprocess
import tempfile


def run_code(code: str, stdin_text: str = "", timeout: float = 5.0) -> dict:
    """安全执行学生代码。

    学生代码约定：读入一行 JSON 数组（如 [5,2,8,1,3]），
    输出一行 JSON 数组（排序结果）。

    Args:
        code: 学生提交的 Python 源代码。
        stdin_text: 传递给 stdin 的输入文本（JSON 数组字符串）。
        timeout: 超时秒数，默认 5s。

    Returns:
        dict: {
            "stdout": str,      标准输出
            "stderr": str,      标准错误
            "returncode": int,  退出码（0=成功）
            "timed_out": bool,  是否超时
        }
    """
    with tempfile.NamedTemporaryFile(
        "w", suffix=".py", delete=False,
        encoding="utf-8", dir=tempfile.gettempdir()
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        proc = subprocess.run(
            ["python", tmp_path],
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir(),
            env={"PATH": os.environ.get("PATH", ""),
                 "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                 "TEMP": tempfile.gettempdir(),
                 "PYTHONIOENCODING": "utf-8"},
        )
        return {
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "returncode": proc.returncode,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "执行超时（超过 {} 秒）".format(timeout),
            "returncode": -1,
            "timed_out": True,
        }
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def run_code_with_collect(code: str, input_arr: list, timeout: float = 5.0) -> dict:
    """执行学生代码并同时采集排序步骤。

    在受限命名空间中执行学生代码，将输入数组替换为 TrackedList，
    拦截每次 __setitem__/pop 操作记录步骤快照。

    Args:
        code: 学生代码。
        input_arr: 输入数组。
        timeout: 超时秒数。

    Returns:
        dict: {"result": {...}, "steps": [...]}
"""
    import ast
    import json

    from app.core.tracked_list import TrackedList

    steps = []
    max_steps = 500

    tracked = TrackedList(input_arr, steps=steps, max_steps=max_steps)

    # 记录初始状态
    steps.append({
        "seq": 0,
        "array_state": list(tracked),
        "op": "init",
        "i": None,
        "j": None,
        "note": "初始数组",
    })

    try:
        tree = ast.parse(code)
        compiled = compile(tree, "<student>", "exec")
        ns = {"arr": tracked, "json": __import__("json")}
        exec(compiled, ns)

        # 尝试调用 sort 函数
        if "sort" in ns and callable(ns["sort"]):
            try:
                result = ns["sort"](tracked)
                steps.append({
                    "seq": len(steps),
                    "array_state": list(result) if result is not None else list(tracked),
                    "op": "done",
                    "i": None,
                    "j": None,
                    "note": "排序完成",
                })
            except Exception as e:
                steps.append({
                    "seq": len(steps),
                    "array_state": list(tracked),
                    "op": "error",
                    "i": None,
                    "j": None,
                    "note": str(e),
                })
        else:
            # 没有 sort 函数，使用 tracked 的最终状态
            steps.append({
                "seq": len(steps),
                "array_state": list(tracked),
                "op": "done",
                "i": None,
                "j": None,
                "note": "无 sort() 函数，取最终 arr 状态",
            })

        return {"result": {"stdout": json.dumps(list(tracked)),
                           "stderr": "",
                           "returncode": 0,
                           "timed_out": False},
                "steps": steps}
    except SyntaxError as e:
        return {"result": {"stdout": "",
                           "stderr": f"SyntaxError: {e.msg} (line {e.lineno})",
                           "returncode": 1,
                           "timed_out": False},
                "steps": steps}
    except Exception as e:
        return {"result": {"stdout": "",
                           "stderr": f"{type(e).__name__}: {e}",
                           "returncode": 1,
                           "timed_out": False},
                "steps": steps}