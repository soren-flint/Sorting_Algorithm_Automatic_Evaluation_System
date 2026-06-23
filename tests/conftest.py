"""pytest 配置与共享 fixtures。"""
import pytest

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    """创建测试 Flask 应用（内存数据库）。"""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    return app


@pytest.fixture(scope="function")
def db(app):
    """每个测试函数独立的数据库。"""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    """Flask 测试客户端。"""
    return app.test_client()


# ---- 共享测试数据 ----

BUBBLE_CODE = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''

QUICK_CODE = '''
def sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr)//2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return sort(left) + mid + sort(right)
'''

MERGE_CODE = '''
def sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = sort(arr[:mid])
    right = sort(arr[mid:])
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
'''

SELECT_CODE = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr
'''

INSERT_CODE = '''
def sort(arr):
    n = len(arr)
    for i in range(1, n):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr
'''

SYNTAX_ERROR_CODE = "def sort(:\n    pass"

INFINITE_LOOP_CODE = "def sort(arr):\n    while True:\n        pass"

OFF_BY_ONE_CODE = '''
def sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i):  # BUG: 应该是 n-1-i
            if j + 1 < n and arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''

STALIN_CODE = '''
def sort(arr):
    if not arr:
        return []
    result = [arr[0]]
    for x in arr[1:]:
        if x >= result[-1]:
            result.append(x)
    return result
'''
