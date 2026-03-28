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


def save_assessment_result(result_id, data, assessment_type='single'):
    """保存评估结果到数据库"""
    from models import AssessmentResult, db

    user_id = get_current_user_id()

    result = AssessmentResult(
        result_id=result_id,
        user_id=user_id,
        assessment_type=assessment_type
    )
    result.set_results(data)

    db.session.add(result)
    db.session.commit()

    return result


def get_user_assessment_history(limit=20):
    """获取用户的评估历史"""
    from models import AssessmentResult

    user_id = get_current_user_id()
    if not user_id:
        return []

    results = AssessmentResult.query.filter_by(user_id=user_id)\
        .order_by(AssessmentResult.created_at.desc())\
        .limit(limit)\
        .all()

    return [r.to_dict() for r in results]


def get_assessment_result_by_id(result_id):
    """根据result_id获取评估结果"""
    from models import AssessmentResult

    result = AssessmentResult.query.filter_by(result_id=result_id).first()

    if result:
        # 验证用户权限
        user_id = get_current_user_id()
        if result.user_id == user_id:
            return result.to_dict()

    return None


def get_user_statistics():
    """获取用户统计信息"""
    from models import AssessmentResult, db
    from sqlalchemy import func

    user_id = get_current_user_id()
    if not user_id:
        return None

    # 总评估次数
    total_count = AssessmentResult.query.filter_by(user_id=user_id).count()

    # 综合评估次数
    comprehensive_count = AssessmentResult.query.filter_by(
        user_id=user_id,
        assessment_type='comprehensive'
    ).count()

    # 单独评估次数
    single_count = AssessmentResult.query.filter_by(
        user_id=user_id,
        assessment_type='single'
    ).count()

    # 最近一次评估时间
    latest_result = AssessmentResult.query.filter_by(user_id=user_id)\
        .order_by(AssessmentResult.created_at.desc())\
        .first()

    latest_date = latest_result.created_at if latest_result else None

    return {
        'total_count': total_count,
        'comprehensive_count': comprehensive_count,
        'single_count': single_count,
        'latest_date': latest_date
    }
