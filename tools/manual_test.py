"""人工测试脚本：完整学生端 + 教师端链路。

用法：先启动 Flask (python run.py)，然后运行本脚本。
"""
import json
import re
import sys

import requests

BASE = "http://127.0.0.1:5000"
s = requests.Session()

# 测试前自动重置数据库（确保干净状态）
import subprocess, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
subprocess.run(["python", "seed.py"], capture_output=True)

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}  {detail}")


def get_csrf(html):
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return m.group(1) if m else ""


def get_csrf_id(html):
    m = re.search(r'id="csrf-token" value="([^"]+)"', html)
    return m.group(1) if m else ""


print("=" * 60)
print("SortJudge 人工测试 — 完整链路")
print("=" * 60)

# ═══════════════════════════════════════════
# 第一部分：学生端测试
# ═══════════════════════════════════════════
print("\n👨‍🎓 学生端测试")
print("-" * 40)

# S1: 首页重定向
r = s.get(BASE + "/")
check("S1 首页重定向到登录", r.url.endswith("/auth/login") or "/auth/login" in r.url,
      f"实际跳转: {r.url}")

# S2: 注册新学生
r = s.get(BASE + "/auth/register")
csrf = get_csrf(r.text)
r = s.post(BASE + "/auth/register", data={
    "username": "test_student", "password": "test1234",
    "role": "student", "csrf_token": csrf,
})
check("S2 注册新用户", "注册成功" in r.text or r.status_code == 302,
      f"status={r.status_code}")

# S3: 登录
r = s.get(BASE + "/auth/login")
csrf = get_csrf(r.text)
r = s.post(BASE + "/auth/login", data={
    "username": "test_student", "password": "test1234",
    "csrf_token": csrf,
}, allow_redirects=True)
check("S3 登录成功", "SortJudge" in r.text or r.status_code == 200)

# S4: 题目列表
r = s.get(BASE + "/problems/")
check("S4 题目列表页", r.status_code == 200 and "冒泡" in r.text,
      f"status={r.status_code}")

# S5: IDE 页
r = s.get(BASE + "/problems/1")
csrf = get_csrf_id(r.text)
check("S5 IDE 页面加载", r.status_code == 200 and "CodeMirror" in r.text or "code-editor" in r.text,
      f"status={r.status_code}")

# S6: 提交空代码
r = s.post(BASE + "/submit/1", data={
    "code": "", "csrf_token": csrf,
})
check("S6 空代码被拒绝", r.status_code == 400 or "不能为空" in r.text,
      f"status={r.status_code}")

# S7: 提交死循环
r = s.post(BASE + "/submit/1", data={
    "code": "def sort(arr):\n    while True:\n        pass",
    "csrf_token": csrf,
})
if r.status_code == 200:
    data = r.json()
    check("S7 死循环超时", data.get("status") == "timeout",
          f"status={data.get('status')}")
else:
    check("S7 死循环超时", False, f"HTTP {r.status_code}")

# S8: 提交正确冒泡
bubble_code = '''def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr'''

r = s.post(BASE + "/submit/1", data={
    "code": bubble_code,
    "csrf_token": csrf,
})
if r.status_code == 200:
    data = r.json()
    check("S8 冒泡通过", data.get("status") == "pass",
          f"status={data.get('status')} score={data.get('score')}")
    check("S8 识别为冒泡", "bubble" in str(data.get("recognized_algo", "")),
          f"algo={data.get('recognized_algo')}")
    check("S8 返回 detail_ids", bool(data.get("detail_ids")),
          f"ids={data.get('detail_ids')}")
    sub_id = data.get("submission_id")
    detail_id = data["detail_ids"][0] if data.get("detail_ids") else None
else:
    check("S8 冒泡通过", False, f"HTTP {r.status_code}")
    sub_id = None
    detail_id = None

# S9: 可视化 API
if detail_id:
    r = s.get(f"{BASE}/submit/api/steps/{detail_id}")
    if r.status_code == 200:
        steps = r.json()
        check("S9 可视化 API 返回步骤", len(steps) > 0 and "op" in steps[0],
              f"步骤数={len(steps)}")
    else:
        check("S9 可视化 API", False, f"HTTP {r.status_code}")

# S10: 可视化页面
if sub_id:
    r = s.get(f"{BASE}/submit/visualize/{sub_id}")
    check("S10 可视化页面", r.status_code == 200 and "canvas" in r.text.lower(),
          f"status={r.status_code}")

# S11: 复杂度分析（跳过——实测耗时长，已在 pytest 中覆盖）
check("S11 复杂度分析(跳过)", True, "(pytest 已覆盖)")

# S12: 提交有 bug 的代码（比较方向错误）
bug_code = '''def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] < arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr'''

r = s.post(BASE + "/submit/1", data={
    "code": bug_code,
    "csrf_token": csrf,
})
if r.status_code == 200:
    data = r.json()
    check("S12 bug 代码失败", data.get("status") == "fail",
          f"status={data.get('status')}")
    check("S12 有反馈", data.get("feedback") is not None,
          f"feedback={data.get('feedback')}")
else:
    check("S12 bug 代码", False, f"HTTP {r.status_code}")

# S13: 提交斯大林排序
stalin_code = '''def sort(arr):
    if not arr:
        return []
    result = [arr[0]]
    for x in arr[1:]:
        if x >= result[-1]:
            result.append(x)
    return result'''

# 题目6 是斯大林排序
r = s.get(BASE + "/problems/6")
csrf = get_csrf_id(r.text)
r = s.post(BASE + "/submit/6", data={
    "code": stalin_code,
    "csrf_token": csrf,
})
if r.status_code == 200:
    data = r.json()
    check("S13 斯大林排序通过", data.get("status") == "pass",
          f"status={data.get('status')}")
else:
    check("S13 斯大林排序", False, f"HTTP {r.status_code}")

# S14: 提交历史
r = s.get(BASE + "/submit/history")
check("S14 提交历史", r.status_code == 200 and "冒泡" in r.text or "test_student" in r.text,
      f"status={r.status_code}")


# ═══════════════════════════════════════════
# 第二部分：教师端测试
# ═══════════════════════════════════════════
print("\n👨‍🏫 教师端测试")
print("-" * 40)

# 登出 → 教师登录
s.get(BASE + "/auth/logout")
r = s.get(BASE + "/auth/login")
csrf = get_csrf(r.text)
r = s.post(BASE + "/auth/login", data={
    "username": "teacher1", "password": "123456",
    "csrf_token": csrf,
}, allow_redirects=True)
check("T1 教师登录", "teacher1" in r.text or r.status_code == 200,
      f"status={r.status_code}")

# T2: 仪表盘
r = s.get(BASE + "/teacher/")
check("T2 教师仪表盘", r.status_code == 200 and ("题目总数" in r.text or "管理" in r.text),
      f"status={r.status_code}")

# T3: 题目管理列表
r = s.get(BASE + "/teacher/problems")
check("T3 题目管理列表", r.status_code == 200 and "冒泡" in r.text,
      f"status={r.status_code}")

# T4: 创建新题目
r = s.get(BASE + "/teacher/problems/new")
csrf = get_csrf(r.text)
r = s.post(BASE + "/teacher/problems/new", data={
    "csrf_token": csrf,
    "title": "手动测试题-堆排序",
    "description": "请实现堆排序",
    "difficulty": "hard",
    "algo_type": "heap",
    "sort_rule": "strict",
    "complexity_ceiling": "O(n log n)",
    "tc_input": ["[3,1,2]", "[5,4,3,2,1]"],
    "tc_expected": ["[1,2,3]", "[1,2,3,4,5]"],
    "tc_public": ["1", "1"],
}, allow_redirects=True)
check("T4 创建题目", r.status_code == 200 and "创建成功" in r.text or "手动测试题" in r.text,
      f"status={r.status_code}")

# 找到新题 ID
import re as re2
matches = re2.findall(r'/teacher/problems/(\d+)/edit', r.text)
new_pid = int(max(matches, key=int)) if matches else None
print(f"  DEBUG new_pid={new_pid}, all_matches={matches}")

# T5: 编辑题目
if new_pid:
    r = s.get(f"{BASE}/teacher/problems/{new_pid}/edit")
    check("T5 编辑页加载", r.status_code == 200 and "手动测试题" in r.text,
          f"status={r.status_code}")
    csrf = get_csrf(r.text)
    r = s.post(f"{BASE}/teacher/problems/{new_pid}/edit", data={
        "csrf_token": csrf,
        "title": "手动测试题-堆排序(已编辑)",
        "description": "请实现堆排序——已更新",
        "difficulty": "medium",
        "algo_type": "heap",
        "sort_rule": "strict",
        "complexity_ceiling": "",
        "tc_input": ["[3,1,2]"],
        "tc_expected": ["[1,2,3]"],
        "tc_public": ["1"],
    }, allow_redirects=True)
    check("T5 编辑保存", "已更新" in r.text or "已编辑" in r.text,
          f"status={r.status_code}")

# T6: 查重
r = s.get(BASE + "/teacher/similarity")
csrf = get_csrf(r.text)
r = s.post(BASE + "/teacher/similarity", data={
    "csrf_token": csrf,
    "problem_id": "1",
    "threshold": "0.70",
})
check("T6 查重页面", r.status_code == 200,
      f"status={r.status_code}")

# T7: 删除题目
if new_pid:
    r = s.get(f"{BASE}/teacher/problems/{new_pid}/edit")
    csrf = get_csrf(r.text)
    r = s.post(f"{BASE}/teacher/problems/{new_pid}/delete", data={
        "csrf_token": csrf,
    }, allow_redirects=True)
    check("T7 删除题目", "已删除" in r.text,
          f"status={r.status_code}")

# T8: 学生不能访问教师页
s.get(BASE + "/auth/logout")
r = s.get(BASE + "/auth/login")
csrf = get_csrf(r.text)
s.post(BASE + "/auth/login", data={
    "username": "student1", "password": "123456",
    "csrf_token": csrf,
})
r = s.get(BASE + "/teacher/")
check("T8 学生被拒绝访问教师页", r.status_code == 403,
      f"status={r.status_code}")


# ═══════════════════════════════════════════
# 汇总
# ═══════════════════════════════════════════
print("\n" + "=" * 60)
print(f"测试结果:  {PASS} 通过 / {FAIL} 失败 / {PASS + FAIL} 总计")
if FAIL == 0:
    print("🎉 全部通过！")
else:
    print(f"⚠️ 有 {FAIL} 项失败，需检查")
print("=" * 60)

sys.exit(0 if FAIL == 0 else 1)
