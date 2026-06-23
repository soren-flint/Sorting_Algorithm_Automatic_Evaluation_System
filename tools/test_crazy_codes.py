# SortJudge 离谱代码全景测试 + 动画验证
import json, re, sys, requests, os

BASE = "http://127.0.0.1:5000"
s = requests.Session()
r = s.get(f"{BASE}/auth/login")
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
r = s.post(f"{BASE}/auth/login", data={'username':'student1','password':'123456','csrf_token':csrf})

codes = {
  "语法错误类": {
    "缺括号": "def sort(arr):\n    return sorted(arr",
    "缩进全乱": "def sort(arr):\nreturn sorted(arr)",
    "中文分号": "def sort(arr)：\n    return sorted(arr)",
    "冒号缺失": "def sort(arr)\n    return sorted(arr)",
    "非法字符": "def sort(arr):\n    return sorted(arr) @@@",
    "空代码": "",
  },
  "运行时错误类": {
    "除零": "def sort(arr):\n    x = 1/0\n    return sorted(arr)",
    "类型混用": "def sort(arr):\n    return sorted(arr) + 'hello'",
    "无限递归": "def sort(arr):\n    return sort(arr)",
    "属性不存在": "def sort(arr):\n    arr.nonexistent()\n    return arr",
    "参数数量错": "def sort(arr, extra):\n    return sorted(arr)",
    "KeyError": "def sort(arr):\n    d={}\n    return d['nonexistent']",
  },
  "安全攻击类": {
    "读取系统文件": "def sort(arr):\n    open('/etc/passwd')\n    return sorted(arr)",
    "执行系统命令": "def sort(arr):\n    __import__('os').system('echo hack')\n    return sorted(arr)",
    "exec注入": "def sort(arr):\n    exec('import os; os.system(\"echo pwned\")')\n    return sorted(arr)",
    "导入危险模块": "def sort(arr):\n    import subprocess\n    return sorted(arr)",
    "compile+exec": "def sort(arr):\n    compile('1+1','','exec')\n    return sorted(arr)",
  },
  "逻辑灾难类": {
    "返回随机数": "def sort(arr):\n    import random\n    random.shuffle(arr)\n    return arr",
    "只返回第一个": "def sort(arr):\n    return [arr[0]] if arr else []",
    "全部返回0": "def sort(arr):\n    return [0]*len(arr)",
    "嵌套自身10层": "def sort(arr):\n    for _ in range(10):\n        arr = sort(arr) if len(arr)>1 else arr\n    return arr",
    "只排序前两个": "def sort(arr):\n    if len(arr)>=2 and arr[0]>arr[1]:\n        arr[0],arr[1]=arr[1],arr[0]\n    return arr",
    "反转数组": "def sort(arr):\n    return list(reversed(arr))",
    "添加额外元素": "def sort(arr):\n    result = sorted(arr)\n    result.append(999)\n    return result",
    "修改全局变量": "x = []\ndef sort(arr):\n    global x\n    x = sorted(arr)\n    return x",
  },
  "资源耗尽类": {
    "双重死循环": "def sort(arr):\n    i = 0\n    while i < 100:\n        j = 0\n        while j < 100:\n            pass",
    "百万次空循环": "def sort(arr):\n    for i in range(1000000):\n        pass\n    return sorted(arr)",
  },
}

PASS = FAIL = 0
for cat, tests in codes.items():
    print(f"\n{'─'*50}")
    print(f"  {cat} ({len(tests)} tests)")
    print(f"{'─'*50}")
    for name, code in tests.items():
        r = s.get(f"{BASE}/problems/1")
        m = re.search(r'id="csrf-token" value="([^"]+)"', r.text)
        if not m:
            print(f"  ❌ {name}: CSRF获取失败"); FAIL += 1; continue
        cr = s.post(f"{BASE}/submit/1", data={'code': code, 'csrf_token': m.group(1)})
        if cr.status_code != 200:
            try: d = cr.json()
            except: d = {"error": cr.text[:80]}
            print(f"  ❌ {name}: HTTP {cr.status_code} | {d.get('error', d)}")
            FAIL += 1
        else:
            d = cr.json()
            st = d.get('status','?')
            # Verify visualization API works for this submission
            did = d.get('detail_ids', [])
            vis_ok = False
            if did:
                vr = s.get(f"{BASE}/submit/api/steps/{did[0]}")
                vis_ok = vr.status_code == 200 and isinstance(vr.json(), list)
            g = d.get('grade', {})
            icon = '✅' if st == 'pass' else ('⚠️' if st == 'fail' else '❌')
            print(f"  {icon} {name}: {st} | grade={g.get('total','?')}/10 | vis={'OK' if vis_ok else 'N/A'} | {g.get('algorithm',{}).get('detected','?')}")
            if st != 'pass' and d.get('feedback'):
                fb = d['feedback']
                print(f"     ↳ [{fb.get('type','')}] {fb.get('hint','')[:90]}")
            PASS += 1

print(f"\n{'='*50}")
print(f"  PASS={PASS}  FAIL={FAIL}  TOTAL={PASS+FAIL}")
print(f"{'='*50}")
