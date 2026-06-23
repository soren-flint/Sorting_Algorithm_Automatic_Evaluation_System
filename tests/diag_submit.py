"""诊断 submit 错误"""
import requests, re

s = requests.Session()

# login
r = s.get('http://127.0.0.1:5000/auth/login')
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
r = s.post('http://127.0.0.1:5000/auth/login',
           data={'username':'student1','password':'123456','csrf_token':csrf})
print('Login:', r.status_code)

# get editor page
r = s.get('http://127.0.0.1:5000/problems/1')
csrf2 = re.search(r'id="csrf-token" value="([^"]+)"', r.text).group(1)
print('Editor token found')

# submit
code = 'def sort(arr):\n    arr.sort()\n    return arr'
r = s.post('http://127.0.0.1:5000/submit/1',
           data={'code':code,'csrf_token':csrf2})
print('Status:', r.status_code)
print('Content-Type:', r.headers.get('Content-Type',''))
print('Response:', r.text[:300])
