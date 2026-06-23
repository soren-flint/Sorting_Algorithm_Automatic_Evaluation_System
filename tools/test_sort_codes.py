# SortJudge 排序代码全面测试
import json, re, sys, requests

BASE = "http://127.0.0.1:5000"
s = requests.Session()

# 登录
r = s.get(f"{BASE}/auth/login")
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
r = s.post(f"{BASE}/auth/login", data={'username':'student1','password':'123456','csrf_token':csrf})

codes = json.load(open('tests/sort_codes.json', encoding='utf-8'))

def submit(name, code, pid=1):
    r = s.get(f"{BASE}/problems/{pid}")
    m = re.search(r'id="csrf-token" value="([^"]+)"', r.text)
    if not m: return None
    csrf2 = m.group(1)
    r = s.post(f"{BASE}/submit/{pid}", data={'code': code, 'csrf_token': csrf2})
    if r.status_code != 200: return {"error": f"HTTP {r.status_code}", "body": r.text[:100]}
    return r.json()

for category, tests in codes.items():
    print(f"\n{'='*50}")
    print(f"  {category}")
    print(f"{'='*50}")
    for name, code in tests.items():
        result = submit(name, code)
        if not result:
            print(f"  ❌ {name}: CSRF token 获取失败")
        elif "error" in result:
            print(f"  ❌ {name}: {result['error']} | {result.get('body','')}")
        else:
            status = result.get('status', '?')
            score = result.get('score', '?')
            grade = result.get('grade', {})
            gtotal = grade.get('total', '?') if grade else '?'
            algo = result.get('recognized_algo', '?')
            icon = '✅' if status == 'pass' else ('⚠️' if status == 'fail' else '❌')
            print(f"  {icon} {name}: status={status} score={score}/100 grade={gtotal}/10 algo={algo}")
            if status != 'pass' and result.get('feedback'):
                fb = result['feedback']
                print(f"      反馈: [{fb.get('type','')}] {fb.get('hint','')[:80]}")

print(f"\n{'='*50}")
print(f"  全部测试完成")
print(f"{'='*50}")
