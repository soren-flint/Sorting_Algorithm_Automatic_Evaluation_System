"""快速单链路测试。"""
import json, re, requests

s = requests.Session()

# 登录
r = s.get('http://127.0.0.1:5000/auth/login')
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
r = s.post('http://127.0.0.1:5000/auth/login',
           data={'username':'student1','password':'123456','csrf_token':csrf})
print('Login:', r.status_code, '(OK)' if r.status_code == 200 else '')

# 获取题目页 CSRF
r = s.get('http://127.0.0.1:5000/problems/1')
csrf2 = re.search(r'id="csrf-token" value="([^"]+)"', r.text)
if not csrf2:
    print('CSRF token not found in editor page')
    print(r.text[:500])
    exit(1)
csrf2 = csrf2.group(1)

# 提交正确代码
code = 'def sort(arr):\n    return sorted(arr)'
r = s.post('http://127.0.0.1:5000/submit/1',
           data={'code':code,'csrf_token':csrf2})
print('Submit:', r.status_code)
if r.status_code == 200:
    d = r.json()
    print('  status:', d.get('status'))
    print('  score:', d.get('score'))
    print('  algo:', d.get('recognized_algo'))
    print('  passed:', d.get('passed'))
    print('  detail_ids:', d.get('detail_ids'))
else:
    print('  Error:', r.text[:300])

print('Done!')
