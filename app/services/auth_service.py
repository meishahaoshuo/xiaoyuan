import threading
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.user import User

_login_attempts = {}
_lock = threading.Lock()

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def check_login_lockout(username):
    with _lock:
        entry = _login_attempts.get(username)
        if not entry:
            return False, 0
        if entry.get('lock_until') and datetime.utcnow() < entry['lock_until']:
            remaining = (entry['lock_until'] - datetime.utcnow()).total_seconds() / 60
            return True, max(1, int(remaining))
        if entry.get('lock_until') and datetime.utcnow() >= entry['lock_until']:
            del _login_attempts[username]
        return False, 0


def record_failed_attempt(username):
    with _lock:
        entry = _login_attempts.get(username, {'count': 0, 'lock_until': None})
        entry['count'] = entry.get('count', 0) + 1
        if entry['count'] >= MAX_ATTEMPTS:
            entry['lock_until'] = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
            _login_attempts[username] = entry
            return True, LOCKOUT_MINUTES
        _login_attempts[username] = entry
        return False, 0


def reset_attempts(username):
    with _lock:
        _login_attempts.pop(username, None)


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


_otp_store = {}
_otp_lock = threading.Lock()


def generate_otp(username):
    otp = str(random.randint(100000, 999999))
    with _otp_lock:
        _otp_store[username] = {
            'otp': otp,
            'expires': datetime.utcnow() + timedelta(minutes=5)
        }
    return otp


def verify_otp(username, otp):
    with _otp_lock:
        entry = _otp_store.get(username)
        if not entry:
            return False, '未找到验证码请求，请重新获取。'
        if datetime.utcnow() > entry['expires']:
            _otp_store.pop(username, None)
            return False, '验证码已过期，请重新获取。'
        if entry['otp'] != otp:
            return False, '验证码不正确。'
        _otp_store.pop(username, None)
        return True, '验证成功。'


def register_user(username, password, phone=None):
    existing = User.active().filter_by(username=username).first()
    if existing:
        return False, '用户名已被注册。', None
    user = User(username=username, phone=phone)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return True, '注册成功！', user


def authenticate_user(username, password):
    is_locked, remaining = check_login_lockout(username)
    if is_locked:
        return False, f'账号已被锁定，请 {remaining} 分钟后再试。', None
    user = User.active().filter_by(username=username).first()
    if not user:
        record_failed_attempt(username)
        return False, '用户名或密码错误。', None
    if user.status == 'DISABLED':
        return False, '该账号已被禁用，请联系管理员。', None
    if not user.check_password(password):
        record_failed_attempt(username)
        return False, '用户名或密码错误。', None
    reset_attempts(username)
    return True, '登录成功！', user


def change_password(user, old_password, new_password):
    if not user.check_password(old_password):
        return False, '旧密码不正确。'
    if len(new_password) < 6:
        return False, '新密码至少需要6个字符。'
    user.set_password(new_password)
    db.session.commit()
    return True, '密码修改成功！'


def reset_password(username, new_password):
    user = User.active().filter_by(username=username).first()
    if not user:
        return False, '用户不存在。'
    if len(new_password) < 6:
        return False, '新密码至少需要6个字符。'
    user.set_password(new_password)
    db.session.commit()
    return True, '密码重置成功，请登录。'
