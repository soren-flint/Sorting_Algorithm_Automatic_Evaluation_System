"""诊断账号登录"""
import sys
sys.path.insert(0, '.')
from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    for u in User.query.all():
        ok_123456 = u.check_password('123456')
        ok_1234 = u.check_password('1234')
        print(f'{u.username}: 123456={ok_123456}, 1234={ok_1234}')
    print(f'Total users: {User.query.count()}')
