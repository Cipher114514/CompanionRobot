# -*- coding: utf-8 -*-
"""
认证相关辅助函数
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request
from flask_login import current_user


def login_required_custom(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'warning')
            return redirect(url_for('login_page', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id():
    """获取当前登录用户ID"""
    from flask_login import current_user
    if current_user.is_authenticated:
        return current_user.id
    return None


