"""
元气充能陪伴平台 - Flask版本
直接使用HTML/CSS/JavaScript，避免Gradio兼容性问题
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import csv
import io
import json

# 导入后端模块
from mindchat_dialogue import IntegratedMindChatSystem
from whisper_asr import WhisperASRManager
from voice_module import VoiceTTS
from assessment_scales import ScaleManager

# 导入危机检测模块
from crisis_detection import CrisisDetector, CrisisResponder, CrisisStorage

# 导入数据库模型
from models import (db, User, AssessmentResult, ChatMessage, SentimentAnalysis,
                    ConversationFeedback, UserStrategyProfile, StrategyUsageLog, init_db)

app = Flask(__name__)

# 配置
app.config.update(
    SECRET_KEY='your-secret-key-change-this-in-production',
    SQLALCHEMY_DATABASE_URI='sqlite:///mental_health.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# 初始化数据库
db.init_app(app)

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'

# 全局模型实例
mindchat_system = None
asr_system = None
sentiment_pipeline = None
tts_system = None
multimodal_analyzer = None
crisis_detector = None
crisis_responder = None
crisis_storage = None

# 创建静态音频目录
AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'static', 'audio')
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login用户加载函数"""
    return User.query.get(int(user_id))


def initialize_models():
    """初始化所有模型"""
    global mindchat_system, asr_system, sentiment_pipeline, tts_system, multimodal_analyzer
    global crisis_detector, crisis_responder, crisis_storage

    print("=" * 60)
    print("初始化元气充能陪伴平台...".center(60))
    print("=" * 60)

    # 1. 文本情绪分析
    try:
        from transformers import pipeline
        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="./models/roberta-base-finetuned-dianping-chinese",
            top_k=None
        )
        print("[OK] 文本情绪分析模型加载成功")
    except Exception as e:
        print(f"[ERROR] 文本情绪分析加载失败: {e}")

    # 2. MindChat 对话系统
    try:
        mindchat_system = IntegratedMindChatSystem()
        print("[OK] MindChat 加载成功")
    except Exception as e:
        print(f"[ERROR] MindChat 加载失败: {e}")

    # 3. Whisper ASR
    try:
        asr_manager = WhisperASRManager(model_size="small")
        asr_system = asr_manager.get_model()
        print("[OK] Whisper ASR 加载成功")
    except Exception as e:
        print(f"[ERROR] Whisper ASR 加载失败: {e}")

    # 4. TTS 语音合成
    try:
        tts_system = VoiceTTS(voice="zh-CN-XiaoxiaoNeural", verbose=False)
        print("[OK] TTS 语音合成加载成功")
    except Exception as e:
        print(f"[ERROR] TTS 加载失败: {e}")

    # 5. 多模态情绪分析
    try:
        from multimodal_sentiment import create_multimodal_analyzer
        multimodal_analyzer = create_multimodal_analyzer(use_adaptive_weights=True)
        print("[OK] 多模态情绪分析系统加载成功（动态权重融合已启用）")
    except Exception as e:
        print(f"[ERROR] 多模态情绪分析加载失败: {e}")
        multimodal_analyzer = None

    # 6. 危机检测与干预系统
    try:
        crisis_detector = CrisisDetector()
        crisis_responder = CrisisResponder(ai_generator=mindchat_system.generate_response if mindchat_system else None)
        crisis_storage = CrisisStorage(db_url='sqlite:///crisis_events.db')
        print("[OK] 危机检测与干预系统加载成功")
    except Exception as e:
        print(f"[ERROR] 危机检测系统加载失败: {e}")
        crisis_detector = None
        crisis_responder = None
        crisis_storage = None

    print("=" * 60)
    print("初始化完成！")
    print("=" * 60)


def analyze_sentiment(text):
    """分析文本情绪"""
    if sentiment_pipeline is None:
        return {"emotion": "neutral", "confidence": 0.0}

    try:
        results = sentiment_pipeline(text)[0]
        top_result = max(results, key=lambda x: x['score'])
        label_map = {
            'positive': 'positive',
            'negative': 'negative',
            'neutral': 'neutral'
        }
        emotion = label_map.get(top_result['label'], 'neutral')
        confidence = top_result['score']
        return {"emotion": emotion, "confidence": confidence}
    except Exception as e:
        print(f"情绪分析错误: {e}")
        return {"emotion": "neutral", "confidence": 0.0}


# ==================== 路由 ====================

# ==================== 认证相关路由 ====================

@app.route('/register')
def register_page():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('scales_page'))
    return render_template('register.html')


@app.route('/login')
def login_page():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('scales_page'))
    return render_template('login.html')


@app.route('/profile')
@login_required
def profile_page():
    """个人中心页面"""
    return render_template('profile.html')


@app.route('/')
def home():
    """首页 - 重定向到量表评估页面"""
    if current_user.is_authenticated:
        return redirect(url_for('scales_page'))
    else:
        return redirect(url_for('login_page'))


@app.route('/chat')
@login_required
def chat_page():
    """疗愈机器人页面"""
    return render_template('chat.html')


@app.route('/favicon.ico')
def favicon():
    """返回空 favicon 避免 404 错误"""
    from flask import Response
    return Response('', mimetype='image/x-icon')


@app.route('/report')
@login_required
def report():
    """诊断报告页面"""
    return render_template('report.html')


@app.route('/trend-analysis')
@login_required
def trend_analysis():
    """综合诊断趋势分析页面"""
    return render_template('trend_analysis.html')


@app.route('/scales')
@login_required
def scales_page():
    """量表选择页面"""
    return render_template('scales.html')


@app.route('/comprehensive')
@login_required
def comprehensive_assessment():
    """综合评估页面"""
    return render_template('comprehensive_assessment.html')


@app.route('/scale/<scale_id>')
@login_required
def scale_test_page(scale_id):
    """量表测试页面"""
    # 验证量表ID是否有效
    scale_info = ScaleManager.get_scale_info(scale_id)
    if not scale_info:
        return "量表不存在", 404
    return render_template('scale_test.html')


@app.route('/scale/result/<result_id>')
@login_required
def scale_result_page(result_id):
    """量表结果页面"""
    assessment = AssessmentResult.query.filter_by(result_id=result_id).first()
    if not assessment:
        return "结果不存在", 404
    return render_template('scale_result.html')


@app.route('/scale/comprehensive-result/<result_id>')
@login_required
def comprehensive_result_page(result_id):
    """综合评估结果页面"""
    assessment = AssessmentResult.query.filter_by(result_id=result_id).first()
    if not assessment:
        return "结果不存在", 404
    return render_template('comprehensive_result.html')


# ==================== 认证相关 API ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册API"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        # 验证输入
        if not username or not email or not password:
            return jsonify({"error": "请填写所有字段"}), 400

        if len(username) < 3 or len(username) > 20:
            return jsonify({"error": "用户名长度必须在3-20个字符之间"}), 400

        if len(password) < 6:
            return jsonify({"error": "密码长度至少为6个字符"}), 400

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "用户名已存在"}), 400

        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "邮箱已被注册"}), 400

        # 创建新用户
        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "注册成功！请登录"
        })

    except Exception as e:
        db.session.rollback()
        print(f"注册错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "注册失败，请稍后重试"}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录API"""
    try:
        data = request.json
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        remember = data.get('remember', False)

        if not username_or_email or not password:
            return jsonify({"error": "请输入用户名和密码"}), 400

        # 查找用户（通过用户名或邮箱）
        user = User.query.filter(
            (User.username == username_or_email) |
            (User.email == username_or_email.lower())
        ).first()

        if not user or not user.check_password(password):
            return jsonify({"error": "用户名或密码错误"}), 401

        # 登录用户
        login_user(user, remember=remember)

        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "登录成功",
            "user": user.to_dict()
        })

    except Exception as e:
        print(f"登录错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "登录失败，请稍后重试"}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """用户登出API"""
    try:
        logout_user()
        return jsonify({"success": True, "message": "已退出登录"})
    except Exception as e:
        return jsonify({"error": "退出失败"}), 500


@app.route('/api/user/info')
@login_required
def get_user_info():
    """获取当前用户信息"""
    return jsonify(current_user.to_dict())


@app.route('/api/user/statistics')
@login_required
def get_user_statistics():
    """获取用户统计信息"""
    try:
        # 总评估次数
        total_count = AssessmentResult.query.filter_by(user_id=current_user.id).count()

        # 综合评估次数
        comprehensive_count = AssessmentResult.query.filter_by(
            user_id=current_user.id,
            assessment_type='comprehensive'
        ).count()

        # 单独评估次数
        single_count = AssessmentResult.query.filter_by(
            user_id=current_user.id,
            assessment_type='single'
        ).count()

        # 最近一次评估时间
        latest_result = AssessmentResult.query.filter_by(user_id=current_user.id)\
            .order_by(AssessmentResult.created_at.desc())\
            .first()

        latest_date = latest_result.created_at.isoformat() if latest_result else None

        return jsonify({
            'total_count': total_count,
            'comprehensive_count': comprehensive_count,
            'single_count': single_count,
            'latest_date': latest_date
        })

    except Exception as e:
        print(f"获取统计信息错误: {e}")
        return jsonify({"error": "获取统计信息失败"}), 500


@app.route('/api/user/history')
@login_required
def get_user_history():
    """获取用户评估历史"""
    try:
        limit = request.args.get('limit', 50, type=int)

        results = AssessmentResult.query.filter_by(user_id=current_user.id)\
            .order_by(AssessmentResult.created_at.desc())\
            .limit(limit)\
            .all()

        history = []
        for r in results:
            result_data = r.get_results()

            # 单独评估
            if r.assessment_type == 'single' and 'scale_id' in result_data:
                scale_id = result_data['scale_id']
                scale_info = ScaleManager.get_scale_info(scale_id)

                history.append({
                    'id': r.id,
                    'result_id': r.result_id,
                    'assessment_type': r.assessment_type,
                    'created_at': r.created_at.isoformat(),
                    'scale_id': scale_id,
                    'scale_name': scale_info['name'] if scale_info else scale_id,
                    'scale_icon': scale_info['icon'] if scale_info else '📋',
                    'score': result_data['result'].get('total_score', 0),
                    'max_score': result_data['result'].get('max_score', 0),
                    'severity': result_data['result'].get('severity', ''),
                    'level': result_data['result'].get('level', ''),
                    'recommendation': result_data['result'].get('recommendation', '')
                })

            # 综合评估
            elif r.assessment_type == 'comprehensive' and 'results' in result_data:
                for scale_result in result_data['results']:
                    scale_id = scale_result.get('scale_id', '')
                    scale_info = ScaleManager.get_scale_info(scale_id)

                    history.append({
                        'id': r.id,
                        'result_id': r.result_id,
                        'assessment_type': r.assessment_type,
                        'created_at': r.created_at.isoformat(),
                        'scale_id': scale_id,
                        'scale_name': scale_info['name'] if scale_info else scale_id,
                        'scale_icon': scale_info['icon'] if scale_info else '📋',
                        'score': scale_result.get('total_score', 0),
                        'max_score': scale_result.get('max_score', 0),
                        'severity': scale_result.get('severity', ''),
                        'level': scale_result.get('level', ''),
                        'recommendation': scale_result.get('recommendation', '')
                    })

        return jsonify({'history': history})

    except Exception as e:
        print(f"获取历史记录错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "获取历史记录失败"}), 500


@app.route('/api/user/scale-history')
@login_required
def get_user_scale_history():
    """获取当前用户的量表评估历史"""
    try:
        # 查询最近的评估记录，限制20条
        results = AssessmentResult.query.filter_by(user_id=current_user.id)\
            .order_by(AssessmentResult.created_at.desc())\
            .limit(20)\
            .all()

        history = []
        for r in results:
            result_data = r.get_results()

            # 格式化日期
            date_str = r.created_at.strftime('%Y-%m-%d %H:%M:%S')

            # 单独评估
            if r.assessment_type == 'single' and 'scale_id' in result_data:
                scale_id = result_data['scale_id']
                scale_info = ScaleManager.get_scale_info(scale_id)
                scale_name = scale_info['name'] if scale_info else scale_id

                history.append({
                    'date': date_str,
                    'type': scale_name,
                    'score': result_data['result'].get('total_score', 0),
                    'severity': result_data['result'].get('severity', '')
                })

            # 综合评估
            elif r.assessment_type == 'comprehensive' and 'results' in result_data:
                # 综合评估包含多个量表，为每个量表创建一条记录
                for scale_result in result_data['results']:
                    scale_id = scale_result.get('scale_id', '')
                    scale_info = ScaleManager.get_scale_info(scale_id)
                    scale_name = scale_info['name'] if scale_info else scale_id

                    history.append({
                        'date': date_str,
                        'type': scale_name,
                        'score': scale_result.get('total_score', 0),
                        'severity': scale_result.get('severity', '')
                    })

        return jsonify({
            'success': True,
            'data': history
        })

    except Exception as e:
        print(f"获取量表历史错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': '获取量表历史失败'
        }), 500


@app.route('/api/user/chat-history')
@login_required
def get_chat_history():
    """获取当前用户的对话历史（按日期分组统计）"""
    try:
        # 按日期分组查询对话记录
        from sqlalchemy import func

        # 查询所有对话消息，按日期分组
        chat_dates = db.session.query(
            func.date(ChatMessage.created_at).label('chat_date'),
            func.count(ChatMessage.id).label('message_count'),
            func.max(ChatMessage.created_at).label('last_update')
        ).filter_by(
            user_id=current_user.id
        ).group_by(
            func.date(ChatMessage.created_at)
        ).order_by(
            func.date(ChatMessage.created_at).desc()
        ).limit(20).all()

        history = []
        for chat_date, message_count, last_update in chat_dates:
            # func.date() 返回的是日期字符串，直接使用
            # 如果是字符串格式，直接使用；如果是日期对象，转换为字符串
            if isinstance(chat_date, str):
                date_str = chat_date
            else:
                date_str = str(chat_date) if chat_date else ''

            # last_update 是 datetime 对象，需要格式化
            last_update_str = last_update.strftime('%Y-%m-%d %H:%M:%S') if last_update else ''

            history.append({
                'date': date_str,
                'message_count': message_count,
                'last_update': last_update_str
            })

        return jsonify({
            'success': True,
            'data': history
        })

    except Exception as e:
        print(f"获取对话历史错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': '获取对话历史失败'
        }), 500


@app.route('/api/user/chat-messages')
@login_required
def get_chat_messages():
    """获取当前用户的详细聊天消息列表"""
    try:
        limit = request.args.get('limit', 100, type=int)

        messages = ChatMessage.query.filter_by(
            user_id=current_user.id
        ).order_by(
            ChatMessage.created_at.desc()
        ).limit(limit).all()

        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg.id,
                'user_message': msg.user_message,
                'bot_response': msg.bot_response,
                'emotion': msg.emotion,
                'confidence': msg.confidence,
                'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S') if msg.created_at else None
            })

        return jsonify({
            'success': True,
            'messages': message_list
        })

    except Exception as e:
        print(f"获取聊天消息错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': '获取聊天消息失败'
        }), 500


@app.route('/api/user/chat-messages/<int:message_id>', methods=['DELETE'])
@login_required
def delete_chat_message(message_id):
    """删除指定的聊天消息"""
    try:
        message = ChatMessage.query.filter_by(
            id=message_id,
            user_id=current_user.id
        ).first()

        if not message:
            return jsonify({
                'success': False,
                'error': '消息不存在或无权删除'
            }), 404

        db.session.delete(message)
        db.session.commit()

        print(f"✓ 用户 {current_user.id} 删除了消息 {message_id}")

        return jsonify({
            'success': True,
            'message': '删除成功'
        })

    except Exception as e:
        db.session.rollback()
        print(f"删除消息错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': '删除失败'
        }), 500


@app.route('/api/user/trend-data')
@login_required
def get_user_trend_data():
    """获取用户历史趋势数据"""
    try:
        # 获取所有评估结果
        results = AssessmentResult.query.filter_by(user_id=current_user.id)\
            .order_by(AssessmentResult.created_at.asc())\
            .all()

        # 按量表分组统计
        scale_data = {
            'phq9': [],
            'abc': [],
            'cars': [],
            'hamd': []
        }

        for r in results:
            result_data = r.get_results()

            # 单独评估
            if r.assessment_type == 'single' and 'scale_id' in result_data:
                scale_id = result_data['scale_id']
                if scale_id in scale_data and 'result' in result_data:
                    scale_data[scale_id].append({
                        'date': r.created_at.isoformat(),
                        'score': result_data['result'].get('total_score', 0),
                        'severity': result_data['result'].get('severity', ''),
                        'level': result_data['result'].get('level', '')
                    })

            # 综合评估
            elif r.assessment_type == 'comprehensive' and 'results' in result_data:
                for scale_result in result_data['results']:
                    scale_id = scale_result.get('scale_id', '')
                    if scale_id in scale_data:
                        scale_data[scale_id].append({
                            'date': r.created_at.isoformat(),
                            'score': scale_result.get('total_score', 0),
                            'severity': scale_result.get('severity', ''),
                            'level': scale_result.get('level', '')
                        })

        # 计算趋势统计
        trend_stats = {}
        for scale_id, data in scale_data.items():
            if len(data) > 0:
                scores = [d['score'] for d in data]
                trend_stats[scale_id] = {
                    'count': len(data),
                    'avg_score': round(sum(scores) / len(scores), 1),
                    'min_score': min(scores),
                    'max_score': max(scores),
                    'latest': data[-1] if data else None,
                    'trend': 'improving' if len(data) >= 2 and scores[-1] < scores[-2] else
                             'stable' if len(data) >= 2 and scores[-1] == scores[-2] else
                             'declining' if len(data) >= 2 else 'unknown'
                }

        # 获取聊天数据
        chat_messages = ChatMessage.query.filter_by(user_id=current_user.id)\
            .order_by(ChatMessage.created_at.asc())\
            .all()

        # 分析聊天情绪趋势
        chat_emotion_data = []
        emotion_counts = {'positive': 0, 'negative': 0, 'neutral': 0}

        # 有效的情绪值
        valid_emotions = {'positive', 'negative', 'neutral'}

        for msg in chat_messages:
            # 验证情绪值是否有效
            emotion = msg.emotion if msg.emotion in valid_emotions else 'neutral'

            chat_emotion_data.append({
                'date': msg.created_at.isoformat(),
                'emotion': emotion,
                'confidence': msg.confidence
            })
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        # 计算最近7天的情绪分布
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_chats = [m for m in chat_messages if m.created_at >= week_ago]
        recent_emotion_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for msg in recent_chats:
            # 验证情绪值是否有效
            emotion = msg.emotion if msg.emotion in valid_emotions else 'neutral'
            recent_emotion_counts[emotion] = recent_emotion_counts.get(emotion, 0) + 1

        return jsonify({
            'scale_data': scale_data,
            'trend_stats': trend_stats,
            'total_assessments': len(results),
            'chat_data': {
                'total_messages': len(chat_messages),
                'emotion_data': chat_emotion_data,
                'emotion_counts': emotion_counts,
                'recent_emotion_counts': recent_emotion_counts,
                'first_chat_date': chat_messages[0].created_at.isoformat() if chat_messages else None,
                'latest_chat_date': chat_messages[-1].created_at.isoformat() if chat_messages else None
            }
        })

    except Exception as e:
        print(f"获取趋势数据错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "获取趋势数据失败"}), 500


@app.route('/api/profile/export')
@login_required
def export_profile_data():
    """导出用户数据为CSV文件"""
    try:
        # 创建内存中的CSV文件
        output = io.StringIO()

        # 获取所有评估结果
        assessment_results = AssessmentResult.query.filter_by(user_id=current_user.id)\
            .order_by(AssessmentResult.created_at.desc())\
            .all()

        # 获取所有对话记录
        chat_messages = ChatMessage.query.filter_by(user_id=current_user.id)\
            .order_by(ChatMessage.created_at.desc())\
            .all()

        # 写入CSV
        writer = csv.writer(output)

        # 写入量表评估结果
        writer.writerow(['===== 量表评估结果 ====='])
        writer.writerow(['日期', '类型', '分数', '详情'])

        for result in assessment_results:
            result_data = result.get_results()
            date_str = result.created_at.strftime('%Y-%m-%d %H:%M:%S')

            # 单独评估
            if result.assessment_type == 'single' and 'scale_id' in result_data:
                scale_id = result_data['scale_id']
                scale_info = ScaleManager.get_scale_info(scale_id)
                scale_name = scale_info['name'] if scale_info else scale_id

                score_data = result_data.get('result', {})
                score = f"{score_data.get('total_score', 0)}/{score_data.get('max_score', 0)}"
                severity = score_data.get('severity', '')
                level = score_data.get('level', '')

                detail = f"{scale_name} - {severity} ({level})"

                writer.writerow([date_str, '单独评估', score, detail])

            # 综合评估
            elif result.assessment_type == 'comprehensive' and 'results' in result_data:
                for scale_result in result_data['results']:
                    scale_id = scale_result.get('scale_id', '')
                    scale_info = ScaleManager.get_scale_info(scale_id)
                    scale_name = scale_info['name'] if scale_info else scale_id

                    score = f"{scale_result.get('total_score', 0)}/{scale_result.get('max_score', 0)}"
                    severity = scale_result.get('severity', '')
                    level = scale_result.get('level', '')

                    detail = f"{scale_name} - {severity} ({level})"

                    writer.writerow([date_str, '综合评估', score, detail])

        # 写入空行分隔
        writer.writerow([])
        writer.writerow(['===== 对话记录 ====='])
        writer.writerow(['日期', '用户消息', 'AI回复', '情绪', '置信度'])

        for msg in chat_messages:
            date_str = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            user_msg = msg.user_message.replace('\n', ' ').replace('\r', '') if msg.user_message else ''
            bot_response = msg.bot_response.replace('\n', ' ').replace('\r', '') if msg.bot_response else ''
            emotion = msg.emotion if msg.emotion else 'neutral'
            confidence = f"{msg.confidence:.4f}" if msg.confidence else '0.0000'

            writer.writerow([date_str, user_msg, bot_response, emotion, confidence])

        # 写入空行分隔
        writer.writerow([])
        writer.writerow(['===== 对话反馈记录 ====='])
        writer.writerow(['日期', '反馈类型', '反馈原因', '详细反馈', '用户情绪'])

        # 获取所有反馈记录
        feedbacks = ConversationFeedback.query.filter_by(user_id=current_user.id)\
            .order_by(ConversationFeedback.created_at.desc())\
            .all()

        for feedback in feedbacks:
            date_str = feedback.created_at.strftime('%Y-%m-%d %H:%M:%S')
            feedback_type = '正面' if feedback.feedback_type == 'positive' else '负面'

            # 翻译反馈原因
            reason_map = {
                'helpful': '有帮助',
                'inappropriate': '内容不当',
                'inaccurate': '理解错误',
                'unclear': '不够清晰',
                'other': '其他问题'
            }
            feedback_reason = reason_map.get(feedback.feedback_reason, feedback.feedback_reason or '-')
            feedback_text = feedback.feedback_text.replace('\n', ' ').replace('\r', '') if feedback.feedback_text else ''
            user_emotion = feedback.user_emotion if feedback.user_emotion else '-'

            writer.writerow([date_str, feedback_type, feedback_reason, feedback_text, user_emotion])

        # 准备文件名
        today = datetime.now().strftime('%Y%m%d')
        filename = f'mental_health_data_{current_user.username}_{today}.csv'

        # 创建文件响应
        output.seek(0)
        response = send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),  # 使用UTF-8 BOM编码以支持Excel
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

        return response

    except Exception as e:
        print(f"导出数据错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "导出数据失败"}), 500


@app.route('/api/scale/<scale_id>/history')
@login_required
def get_scale_history(scale_id):
    """获取特定量表的历史记录"""
    try:
        results = AssessmentResult.query.filter_by(user_id=current_user.id)\
            .order_by(AssessmentResult.created_at.desc())\
            .all()

        history = []
        for r in results:
            result_data = r.get_results()

            # 单独评估
            if r.assessment_type == 'single' and 'scale_id' in result_data:
                if result_data['scale_id'] == scale_id:
                    history.append({
                        'result_id': r.result_id,
                        'date': r.created_at.isoformat(),
                        'score': result_data['result'].get('total_score', 0),
                        'severity': result_data['result'].get('severity', ''),
                        'level': result_data['result'].get('level', ''),
                        'recommendation': result_data['result'].get('recommendation', ''),
                        'max_score': result_data['result'].get('max_score', 0)
                    })

            # 综合评估
            elif r.assessment_type == 'comprehensive' and 'results' in result_data:
                for scale_result in result_data['results']:
                    if scale_result.get('scale_id') == scale_id:
                        history.append({
                            'result_id': r.result_id,
                            'date': r.created_at.isoformat(),
                            'score': scale_result.get('total_score', 0),
                            'severity': scale_result.get('severity', ''),
                            'level': scale_result.get('level', ''),
                            'recommendation': scale_result.get('recommendation', ''),
                            'max_score': scale_result.get('max_score', 0)
                        })

        return jsonify({'history': history})

    except Exception as e:
        print(f"获取量表历史错误: {e}")
        return jsonify({"error": "获取量表历史失败"}), 500


@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """处理聊天请求"""
    data = request.json
    message = data.get('message', '').strip()

    # 验证消息不为空且有实际内容
    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    # 检查消息长度（防止极短无效输入）
    if len(message) < 2:
        return jsonify({"error": "消息内容太短，请重新输入"}), 400

    try:
        # 1. 分析情绪
        emotion_data = analyze_sentiment(message)

        # 1.5. 危机检测（新增）
        crisis_detected = False
        crisis_level = 0
        crisis_response_data = None

        if crisis_detector:
            try:
                # 执行危机检测
                detection_result = crisis_detector.detect(
                    user_input=message,
                    user_id=current_user.id,
                    voice_emotion=None,  # 暂不支持语音输入
                    scale_scores=None     # 会自动从数据库获取
                )

                # 如果检测到危机
                if detection_result.is_crisis:
                    crisis_detected = True
                    crisis_level = detection_result.level

                    print(f"[危机检测] 用户 {current_user.id}: 检测到危机等级 {crisis_level}")
                    print(f"  关键词: {detection_result.keywords}")
                    print(f"  置信度: {detection_result.confidence:.2f}")
                    print(f"  建议行动: {detection_result.suggested_action}")

                    # 记录到危机事件数据库
                    if crisis_storage:
                        try:
                            crisis_storage.log_event(detection_result, current_user.id)
                        except Exception as e:
                            print(f"记录危机事件失败: {e}")

                    # 生成危机干预回复
                    if crisis_responder:
                        intervention = crisis_responder.generate(
                            level=detection_result.level,
                            keywords=detection_result.keywords,
                            emotion=emotion_data.get("emotion"),
                            user_input=message,
                            user_context={"user_id": current_user.id}
                        )
                        crisis_response_data = intervention

                        # 如果需要覆盖正常回复（2级及以上）
                        if intervention.should_cover:
                            print(f"[危机干预] 使用干预回复覆盖正常回复")
                            response = intervention.content

                            # 保存聊天记录
                            chat_message = ChatMessage(
                                user_id=current_user.id,
                                user_message=message,
                                bot_response=response,
                                emotion=emotion_data["emotion"],
                                confidence=emotion_data["confidence"],
                                is_crisis_response=True  # 标记为危机回复
                            )
                            db.session.add(chat_message)
                            db.session.commit()

                            return jsonify({
                                "response": response,
                                "emotion": emotion_data,
                                "audio_path": None,
                                "crisis_detected": True,
                                "crisis_level": crisis_level,
                                "crisis_intervention": True
                            })

            except Exception as e:
                print(f"危机检测失败: {e}")
                import traceback
                traceback.print_exc()

        # 2. 获取用户策略（如果有）
        strategy_used = "default"
        strategy_name = "默认"

        try:
            from models import UserStrategyProfile
            strategy_profile = UserStrategyProfile.query.filter_by(user_id=current_user.id).first()

            if strategy_profile and strategy_profile.preferred_style:
                strategy_used = strategy_profile.preferred_style

                # 获取风格名称
                from personalized_healing import UserProfile
                if strategy_used in UserProfile.CONVERSATION_STYLES:
                    strategy_name = UserProfile.CONVERSATION_STYLES[strategy_used]['name']
                elif strategy_used == 'auto':
                    strategy_name = '自动推荐'
        except Exception as e:
            print(f"获取用户策略失败: {e}")

        # 3. 生成动态prompt（优化版：病耻感友好 + 精简高效）
        dynamic_prompt = None
        try:
            from dynamic_prompt_generator import DynamicPromptGenerator
            prompt_generator = DynamicPromptGenerator(current_user.id, stigma_aware=True)
            dynamic_prompt = prompt_generator.generate_system_prompt()

            # 记录调试信息
            time_context = prompt_generator.get_current_time_period()
            emotion_context = prompt_generator.get_emotion_context()

            print(f"[动态Prompt v2.1] 用户 {current_user.id}:")
            print(f"  病耻感友好模式: ✅ 启用")
            print(f"  Prompt类型: 精简优化版")
            print(f"  最近情绪: {emotion_context['recent_emotions']}")
            print(f"  情绪状态: {emotion_context['state_description']}")
            print(f"  时间: {time_context['period_name']}")
            print(f"  Prompt长度: {len(dynamic_prompt)} 字符")

            # 检查Prompt长度
            if len(dynamic_prompt) > 800:
                print(f"  ⚠️ 警告：Prompt偏长，可能影响回复完整性")
            elif len(dynamic_prompt) < 400:
                print(f"  ✅ Prompt长度优秀")
            else:
                print(f"  ✅ Prompt长度合理")

        except Exception as e:
            print(f"[动态Prompt] 生成失败，使用默认prompt: {e}")
            import traceback
            traceback.print_exc()

        # 4. 生成回复（使用动态prompt，传入user_id）
        result = mindchat_system.analyze_and_respond(message, system_prompt=dynamic_prompt, user_id=current_user.id)

        if result.get("success"):
            response = result["response"]

            # 获取引导问题
            follow_up_questions = result.get("follow_up_questions", [])

            # 4.5. 应用个性化策略（基于用户反馈）
            try:
                from personalized_dialogue import personalized_strategy
                response = personalized_strategy.adjust_response_style(current_user.id, response)
            except Exception as e:
                print(f"个性化策略应用失败: {e}")

            # 清理回复 - 优化版：只移除明显的重复开头，保留完整内容
            unwanted_prefixes = [
                "你好！有什么可以帮助你的吗？",
                "你好，有什么可以帮助你的吗？",
                "你好！请问有什么可以帮你的？",
                "你好，请问有什么可以帮你的？",
            ]
            for prefix in unwanted_prefixes:
                if response.startswith(prefix):
                    response = response[len(prefix):].strip()
                    print(f"[聊天] 移除前缀: '{prefix}'")
                    break

            # 智能长度限制：如果超过150字，在第一个句号、问号或感叹号处截断
            if len(response) > 150:
                # 在前150字内找合适的截断点
                truncate_point = 150
                for i, char in enumerate(response[100:150]):
                    if char in ['。', '！', '？', '.', '!', '?']:
                        truncate_point = 100 + i + 1
                        break

                if truncate_point < len(response):
                    original_length = len(response)
                    response = response[:truncate_point]
                    print(f"[聊天] 智能截断: {original_length} → {truncate_point} 字符")

            # 保存聊天记录到数据库（保存完整的原始响应）
            chat_message = ChatMessage(
                user_id=current_user.id,
                user_message=message,
                bot_response=response if response else "我在听，请继续说。",
                emotion=emotion_data["emotion"],
                confidence=emotion_data["confidence"]
            )
            db.session.add(chat_message)
            db.session.commit()
            print(f"[聊天] 保存消息 ID: {chat_message.id}, 响应长度: {len(response)} 字符")

            # 生成TTS音频
            audio_path = None
            if tts_system and response:
                try:
                    audio_file = tts_system.synthesize(response)
                    if audio_file and os.path.exists(audio_file):
                        # 复制到静态目录
                        import shutil
                        audio_filename = f"response_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.wav"
                        static_audio_path = os.path.join(AUDIO_DIR, audio_filename)
                        shutil.copy(audio_file, static_audio_path)
                        audio_path = f"/static/audio/{audio_filename}"
                except Exception as e:
                    print(f"TTS生成错误: {e}")

            return jsonify({
                "success": True,
                "response": response if response else "我在听，请继续说。",
                "emotion": emotion_data["emotion"],
                "confidence": emotion_data["confidence"],
                "audio_path": audio_path,
                "chat_message_id": chat_message.id,  # 返回消息ID用于反馈
                "strategy_used": strategy_used,
                "strategy_name": strategy_name,
                "dynamic_prompt_enabled": dynamic_prompt is not None,  # 是否启用动态prompt
                "follow_up_questions": follow_up_questions,  # 添加引导问题
                "debug_info": {
                    "depression_level": prompt_generator.get_depression_level() if dynamic_prompt else None,
                    "time_period": prompt_generator.get_current_time_period()['period'] if dynamic_prompt else None,
                    "emotion_state": prompt_generator.get_emotion_context()['state_description'] if dynamic_prompt else None,
                    "recent_emotions": prompt_generator.get_emotion_context()['recent_emotions'] if dynamic_prompt else None,
                    "prompt_length": len(dynamic_prompt) if dynamic_prompt else 0
                } if dynamic_prompt else None
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "生成回复失败"),
                "response": "抱歉，我暂时无法回复。"
            })

    except Exception as e:
        print(f"对话错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "response": "抱歉，生成回复时出错。"
        }), 500


@app.route('/api/audio', methods=['POST'])
def transcribe_audio():
    """转录音频并提取语音特征"""
    if 'audio' not in request.files:
        return jsonify({"error": "没有音频文件"}), 400

    audio_file = request.files['audio']

    if asr_system is None:
        return jsonify({"error": "语音识别未加载"}), 500

    try:
        # 从上传的文件名中提取扩展名
        filename = audio_file.filename
        file_ext = '.webm'  # 默认
        if filename and '.' in filename:
            file_ext = '.' + filename.rsplit('.', 1)[1].lower()

        # 保存临时文件 - 使用原始文件扩展名
        import tempfile
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        tmp_file.write(audio_file.read())
        tmp_file.flush()  # 确保数据写入磁盘
        audio_path = tmp_file.name
        tmp_file.close()  # 显式关闭文件，确保在Windows上释放文件句柄

        # 检查文件大小（作为双重保险）
        file_size = os.path.getsize(audio_path)
        if file_size < 2000:  # 小于2KB说明录音太短或无效
            os.remove(audio_path)
            return jsonify({
                "success": False,
                "error": f"录音时间太短（文件仅 {file_size} bytes），请至少说话 1 秒"
            }), 400

        # 使用新方法转录并提取特征
        asr_manager = WhisperASRManager(model_size="small")
        result = asr_manager.transcribe_with_features(audio_path)

        # 清理临时文件
        try:
            os.remove(audio_path)
        except:
            pass

        if result.get("success"):
            response_data = {
                "success": True,
                "text": result["text"],
                "transcription_time": result.get("transcription_time", 0)
            }

            # 如果成功提取了语音特征，也返回
            if result.get("audio_features"):
                features = result["audio_features"]
                response_data["audio_features"] = {
                    "pitch_mean": features.get("pitch_mean", 0),
                    "pitch_std": features.get("pitch_std", 0),
                    "tempo": features.get("tempo", 0),
                    "energy": features.get("energy", 0),
                    "shimmer": features.get("shimmer", 0),
                    "duration": features.get("duration", 0)
                }

                # 如果特征提取成功，打印解读信息
                if features.get("success"):
                    from voice_features import interpret_features
                    interpretation = interpret_features(features)
                    print(f"[ASR] 心理健康评估: {interpretation}")

            return jsonify(response_data)
        else:
            return jsonify({"error": result.get('error', '识别失败')}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat/multimodal-sentiment', methods=['POST'])
@login_required
def analyze_multimodal_sentiment():
    """
    多模态情绪分析API（支持动态权重融合）

    接收:
        text: 用户输入的文本（来自ASR或直接输入）
        audio_features: (可选) 语音特征字典
        audio_path: (可选) 音频文件路径

    返回:
        {
            "success": true,
            "overall_sentiment": "negative",
            "confidence": 0.89,
            "text_contribution": 0.75,
            "voice_contribution": 0.92,
            "depression_risk": 0.75,
            "fusion_details": {
                "text_weight": 0.35,
                "voice_weight": 0.65,
                "weight_explanation": [...]
            },
            "audio_quality": {...},
            "risk_indicators": {...}
        }
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        audio_features = data.get('audio_features')
        audio_path = data.get('audio_path')

        if not text:
            return jsonify({'error': '缺少文本内容'}), 400

        # 检查多模态分析器是否可用
        if multimodal_analyzer is None:
            return jsonify({'error': '多模态情绪分析系统未加载'}), 500

        # 使用多模态分析器
        result = multimodal_analyzer.analyze_multimodal(
            text=text,
            audio_features=audio_features,
            audio_path=audio_path
        )

        # 保存分析记录到数据库
        sentiment_analysis = SentimentAnalysis(
            user_id=current_user.id,
            text_sentiment=result.get('fusion_details', {}).get('text_sentiment'),
            text_confidence=result.get('fusion_details', {}).get('text_confidence'),
            voice_sentiment=result.get('fusion_details', {}).get('voice_sentiment'),
            voice_confidence=result.get('fusion_details', {}).get('voice_confidence'),
            overall_sentiment=result.get('overall_sentiment'),
            overall_confidence=result.get('confidence'),
            risk_indicators=json.dumps(result.get('risk_indicators')) if result.get('risk_indicators') else None,
            audio_features=json.dumps(audio_features) if audio_features else None
        )
        db.session.add(sentiment_analysis)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        print(f"多模态情绪分析失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/feedback', methods=['POST'])
@login_required
def submit_chat_feedback():
    """
    提交对话反馈API - 用于RLHF轻量级实现

    接收:
        chat_message_id: 对话消息ID
        feedback_type: 反馈类型 ('positive' 或 'negative')
        feedback_reason: 反馈原因（可选）
            - 'helpful': 有帮助
            - 'inappropriate': 内容不当
            - 'inaccurate': 理解错误
            - 'unclear': 不够清晰
            - 'other': 其他
        feedback_text: 详细反馈文本（可选）

    返回:
        {
            "success": true,
            "feedback_id": 123
        }
    """
    try:
        data = request.get_json()
        chat_message_id = data.get('chat_message_id')
        feedback_type = data.get('feedback_type')
        feedback_reason = data.get('feedback_reason')
        feedback_text = data.get('feedback_text', '')

        # 验证必要参数
        if not chat_message_id or not feedback_type:
            return jsonify({'error': '缺少必要参数'}), 400

        if feedback_type not in ['positive', 'negative']:
            return jsonify({'error': '反馈类型无效'}), 400

        # 验证反馈原因
        valid_reasons = ['helpful', 'inappropriate', 'inaccurate', 'unclear', 'other', None]
        if feedback_reason not in valid_reasons:
            return jsonify({'error': '反馈原因无效'}), 400

        # 查找对话消息
        chat_message = ChatMessage.query.filter_by(id=chat_message_id, user_id=current_user.id).first()
        if not chat_message:
            return jsonify({'error': '对话消息不存在'}), 404

        # 检查是否已经反馈过
        existing_feedback = ConversationFeedback.query.filter_by(
            chat_message_id=chat_message_id,
            user_id=current_user.id
        ).first()

        if existing_feedback:
            # 更新现有反馈
            existing_feedback.feedback_type = feedback_type
            existing_feedback.feedback_reason = feedback_reason
            existing_feedback.feedback_text = feedback_text
            existing_feedback.user_emotion = chat_message.emotion
            db.session.commit()
            return jsonify({
                'success': True,
                'feedback_id': existing_feedback.id,
                'updated': True
            })

        # 创建新反馈
        feedback = ConversationFeedback(
            user_id=current_user.id,
            chat_message_id=chat_message_id,
            feedback_type=feedback_type,
            feedback_reason=feedback_reason,
            feedback_text=feedback_text,
            user_emotion=chat_message.emotion
        )

        db.session.add(feedback)
        db.session.commit()

        print(f"[FEEDBACK] 用户 {current_user.username} 提交反馈: {feedback_type} - {feedback_reason}")

        return jsonify({
            'success': True,
            'feedback_id': feedback.id,
            'updated': False
        })

    except Exception as e:
        print(f"提交反馈失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== 量表相关 API ====================

@app.route('/api/scale/<scale_id>')
def get_scale_data(scale_id):
    """获取量表数据"""
    scale_info = ScaleManager.get_scale_info(scale_id)
    if not scale_info:
        return jsonify({"error": "量表不存在"}), 404

    return jsonify({
        "info": {
            "name": scale_info["name"],
            "full_name": scale_info["full_name"],
            "description": scale_info["description"],
            "target_population": scale_info["target_population"],
            "time_required": scale_info["time_required"],
            "icon": scale_info["icon"]
        },
        "questions": scale_info["questions"]
    })


@app.route('/api/scale/submit', methods=['POST'])
def submit_scale_answers():
    """提交量表答案"""
    try:
        data = request.json
        scale_id = data.get('scale_id')
        answers = data.get('answers')

        if not scale_id or not answers:
            return jsonify({"error": "缺少必要参数"}), 400

        # 将字符串键转换为整数（JSON序列化会将键转为字符串）
        answers = {int(k): v for k, v in answers.items()}

        # 验证量表ID
        scale_info = ScaleManager.get_scale_info(scale_id)
        if not scale_info:
            return jsonify({"error": "量表不存在"}), 404

        # 验证答案完整性
        if not ScaleManager.validate_answers(scale_id, answers):
            # 找出未回答的问题
            missing_questions = []
            for question in scale_info["questions"]:
                if question["id"] not in answers:
                    missing_questions.append(question["id"])
            return jsonify({
                "error": f"答案不完整，还有 {len(missing_questions)} 道题未回答"
            }), 400

        # 计算分数
        result = ScaleManager.calculate_score(scale_id, answers)

        # 生成结果详情
        answers_detail = []
        for question in scale_info["questions"]:
            question_id = question["id"]
            answer_value = answers.get(question_id)

            # 找到对应的选项文本
            option_text = "未回答"
            for option in question["options"]:
                if option["value"] == answer_value:
                    option_text = option["text"]
                    break

            answers_detail.append({
                "question_id": question_id,
                "question": question["question"],
                "answer": option_text,
                "score": answer_value
            })

        # 保存评估结果到数据库
        import uuid
        result_id = str(uuid.uuid4())

        # 创建数据库记录
        assessment_result = AssessmentResult(
            result_id=result_id,
            user_id=current_user.id if current_user.is_authenticated else None,
            assessment_type='single'
        )

        # 准备结果数据
        result_data = {
            "scale_id": scale_id,
            "result": result,
            "answers_detail": answers_detail,
            "timestamp": datetime.now().isoformat()
        }
        assessment_result.set_results(result_data)

        db.session.add(assessment_result)
        db.session.commit()

        return jsonify({
            "success": True,
            "result_id": result_id,
            "result": result
        })

    except Exception as e:
        db.session.rollback()
        print(f"提交答案错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/scale/result/<result_id>')
def get_scale_result(result_id):
    """获取量表结果"""
    assessment = AssessmentResult.query.filter_by(result_id=result_id).first()

    if not assessment:
        return jsonify({"error": "结果不存在"}), 404

    # 验证用户权限（如果有用户登录）
    if current_user.is_authenticated and assessment.user_id != current_user.id:
        return jsonify({"error": "无权访问此结果"}), 403

    # 解析结果数据
    result_data = assessment.get_results()
    result_data['result_id'] = result_id

    return jsonify(result_data)


@app.route('/api/scales/list')
def list_scales():
    """获取所有量表列表"""
    scales = ScaleManager.get_all_scales()
    scale_list = []

    for scale_id, info in scales.items():
        scale_list.append({
            "id": scale_id,
            "name": info["name"],
            "full_name": info["full_name"],
            "description": info["description"],
            "target_population": info["target_population"],
            "time_required": info["time_required"],
            "icon": info["icon"],
            "question_count": len(info["questions"])
        })

    return jsonify({"scales": scale_list})


@app.route('/api/scale/comprehensive', methods=['POST'])
def submit_comprehensive_assessment():
    """提交综合评估（所有量表）"""
    try:
        data = request.json
        answers_dict = data.get('answers')

        if not answers_dict:
            return jsonify({"error": "缺少答案数据"}), 400

        results = []
        detailed_results = []
        scale_info_map = ScaleManager.get_all_scales()

        # 处理每个量表
        for scale_id, answers in answers_dict.items():
            # 将字符串键转换为整数
            answers = {int(k): v for k, v in answers.items()}

            # 验证量表
            scale_info = scale_info_map.get(scale_id)
            if not scale_info:
                return jsonify({"error": f"量表 {scale_id} 不存在"}), 404

            # 验证答案完整性
            if not ScaleManager.validate_answers(scale_id, answers):
                return jsonify({"error": f"{scale_info['name']} 量表答案不完整"}), 400

            # 计算分数
            result = ScaleManager.calculate_score(scale_id, answers)
            result['scale_id'] = scale_id
            result['icon'] = scale_info['icon']
            results.append(result)

            # 生成详细答案
            answers_detail = []
            for question in scale_info["questions"]:
                question_id = question["id"]
                answer_value = answers.get(question_id)

                option_text = "未回答"
                for option in question["options"]:
                    if option["value"] == answer_value:
                        option_text = option["text"]
                        break

                answers_detail.append({
                    "question_id": question_id,
                    "question": question["question"],
                    "answer": option_text,
                    "score": answer_value
                })

            detailed_results.append({
                "scale_id": scale_id,
                "scale_name": result["scale_name"],
                "answers_detail": answers_detail
            })

        # 保存综合评估结果到数据库
        import uuid
        result_id = str(uuid.uuid4())

        # 创建数据库记录
        assessment_result = AssessmentResult(
            result_id=result_id,
            user_id=current_user.id if current_user.is_authenticated else None,
            assessment_type='comprehensive'
        )

        # 准备结果数据
        result_data = {
            "results": results,
            "detailed_results": detailed_results,
            "timestamp": datetime.now().isoformat()
        }
        assessment_result.set_results(result_data)

        db.session.add(assessment_result)
        db.session.commit()

        return jsonify({
            "success": True,
            "result_id": result_id
        })

    except Exception as e:
        db.session.rollback()
        print(f"综合评估提交错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/scale/comprehensive-result/<result_id>')
def get_comprehensive_result(result_id):
    """获取综合评估结果"""
    assessment = AssessmentResult.query.filter_by(result_id=result_id).first()

    if not assessment:
        return jsonify({"error": "结果不存在"}), 404

    # 验证用户权限（如果有用户登录）
    if current_user.is_authenticated and assessment.user_id != current_user.id:
        return jsonify({"error": "无权访问此结果"}), 403

    # 解析结果数据
    result_data = assessment.get_results()
    result_data['result_id'] = result_id
    result_data['timestamp'] = assessment.created_at.isoformat()

    return jsonify(result_data)


@app.route('/api/scale/generate-ai-report/<result_id>')
@login_required
def generate_ai_report(result_id):
    """
    使用AI动态生成评估报告

    基于评估结果，使用MindChat模型生成个性化的综合分析报告
    """
    try:
        assessment = AssessmentResult.query.filter_by(result_id=result_id).first()

        if not assessment:
            return jsonify({"error": "结果不存在"}), 404

        # 验证用户权限
        if assessment.user_id != current_user.id:
            return jsonify({"error": "无权访问此结果"}), 403

        # 解析结果数据
        result_data = assessment.get_results()

        # 构建prompt，让AI生成报告
        prompt = f"""请基于以下心理评估结果，生成一份温暖、亲切、易懂的个人健康报告。

## 评估结果概况：

"""

        # 添加每个量表的评估结果
        for scale_result in result_data.get('results', []):
            scale_name = scale_result.get('scale_name', '未知量表')
            score = scale_result.get('total_score', 0)
            max_score = scale_result.get('max_score', 0)
            severity = scale_result.get('severity', '未知')
            level = scale_result.get('level', '未知')

            prompt += f"""
### {scale_name}
- 得分：{score}/{max_score}
- 状态：{severity}
"""

        prompt += """

## 要求：

请生成一份**写给用户自己看的**贴心报告，就像一位关心的朋友在和TA聊天：

**重要原则**：
- 用第二人称"您"直接对话，不要用"用户""受测者"等冷冰冰的词
- 像朋友聊天一样自然，不要像医疗报告那样严肃
- 多给予鼓励和肯定，少用专业术语
- 强调积极的一面和改善的可能性，而不是只指出问题

**报告内容**：

1. **🌟 给您的拥抱**（150-200字）：
   - 用温暖的语气回应评估结果
   - 肯定TA关注自己心理健康的积极行为
   - 让TA感受到被理解和支持

2. **💡 一起看看结果**（300-400字）：
   - 用生活化的语言解释各项评估结果
   - 帮助TA理解这些数字背后的含义
   - 指出积极方面和需要关注的地方
   - 不要制造焦虑，而是理性客观地说明情况

3. **🌱 我们可以这样做**（300-400字）：
   - 给出2-3个具体、简单、可操作的小建议
   - 用"建议您..."而不是"应该..."的语气
   - 包含日常生活中的小改变（睡眠、运动、社交等）
   - 说明什么时候需要寻求专业帮助（用轻松的方式表达）

4. **💪 您并不孤单**（100-150字）：
   - 温暖的鼓励话语
   - 强调改善是可以实现的
   - 传递希望和信心
   - 让TA感受到支持的力量

**语气要求**：
- 温暖、亲切、真诚
- 避免使用"患者""症状""诊断""治疗"等医疗词汇
- 多用"感受""状态""心情""调整"等生活化词汇
- 适当使用emoji增加亲和力（🌟💡🌱💪😊等）

请使用markdown格式输出。
"""

        # 使用MindChat生成报告
        if mindchat_system is None:
            return jsonify({
                "success": False,
                "error": "AI对话系统未加载，无法生成报告"
            }), 500

        # 对于报告生成，使用更大的max_length（2048 tokens，约1500-2000中文字）
        result = mindchat_system.mindchat.chat(
            prompt,
            system_prompt="你是一位温暖亲切的心理健康陪伴者，擅长用朋友般的语气和用户交流，让用户感受到被理解、被关心、被支持。你写的报告不是冷冰冰的医疗报告，而是充满温度的贴心话。请生成完整的分析报告，不要截断。",
            max_length=2048,  # 设置更大的生成长度
            temperature=0.8,
            user_id=current_user.id
        )

        # 构造返回结果
        ai_report = result if isinstance(result, str) else str(result)

        return jsonify({
            "success": True,
            "ai_report": ai_report,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        print(f"生成AI报告错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/generate-trend-ai-report', methods=['POST'])
@login_required
def generate_trend_ai_report():
    """
    生成趋势分析AI报告

    基于用户的历史评估数据和对话数据，使用AI生成趋势分析报告
    """
    try:
        data = request.json
        prompt = data.get('prompt', '')
        trend_data = data.get('trend_data', {})

        if not prompt:
            return jsonify({
                "success": False,
                "error": "缺少prompt参数"
            }), 400

        # 使用MindChat生成报告
        if mindchat_system is None:
            return jsonify({
                "success": False,
                "error": "AI对话系统未加载，无法生成报告"
            }), 500

        # 对于趋势分析报告生成，使用更大的max_length（2048 tokens）
        result = mindchat_system.mindchat.chat(
            prompt,
            system_prompt="你是一位温暖亲切的心理健康陪伴者，擅长用朋友般的语气和用户交流，让用户感受到被理解、被关心、被支持。你写的报告不是冷冰冰的分析报告，而是充满温度的贴心话，就像一位关心的朋友在和TA回顾这段旅程。请生成完整的分析报告，不要截断。",
            max_length=2048,  # 设置更大的生成长度
            temperature=0.8,
            user_id=current_user.id
        )

        # 构造返回结果
        ai_report = result if isinstance(result, str) else str(result)

        return jsonify({
            "success": True,
            "ai_report": ai_report,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        print(f"生成趋势AI报告错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 个性化疗愈策略系统 ====================

@app.route('/api/strategy/get')
@login_required
def get_strategy():
    """获取用户的疗愈策略"""
    try:
        from personalized_healing import StrategyRecommender

        recommender = StrategyRecommender(current_user.id)
        strategy = recommender.generate_strategy_report()

        return jsonify({
            'success': True,
            'data': strategy
        })
    except Exception as e:
        print(f"获取策略错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/strategy/profile')
@login_required
def get_user_profile():
    """获取用户画像"""
    try:
        # 首先尝试从数据库获取已保存的策略
        strategy_profile = UserStrategyProfile.query.filter_by(user_id=current_user.id).first()

        if strategy_profile and strategy_profile.preferred_style:
            # 如果有已保存的策略，直接使用
            profile = {
                'user_id': current_user.id,
                'recommended_style': strategy_profile.preferred_style,
                'depression_level': {
                    'level': strategy_profile.depression_level or 'unknown',
                    'level_name': strategy_profile.depression_level or '未知'
                },
                'trend': {
                    'status': strategy_profile.trend_status or 'new_user',
                    'status_name': strategy_profile.trend_status or '新用户'
                }
            }

            # 如果有完整画像数据，使用它
            if strategy_profile.profile_data:
                try:
                    import json
                    full_profile = json.loads(strategy_profile.profile_data)
                    profile.update(full_profile)
                except:
                    pass

            print(f"✓ 从数据库加载用户 {current_user.id} 的策略: {strategy_profile.preferred_style}")
            return jsonify({
                'success': True,
                'data': profile
            })
        else:
            # 如果没有保存的策略，生成新的
            from personalized_healing import UserProfiler
            profiler = UserProfiler(current_user.id)
            profile = profiler.generate_profile()

            # 保存到数据库
            if not strategy_profile:
                strategy_profile = UserStrategyProfile(user_id=current_user.id)
                db.session.add(strategy_profile)

            strategy_profile.preferred_style = profile.get('recommended_style', 'guidance')
            strategy_profile.depression_level = profile['depression_level'].get('level', 'unknown')
            strategy_profile.trend_status = profile['trend'].get('status', 'new_user')
            strategy_profile.set_profile(profile)

            db.session.commit()

            print(f"✓ 生成并保存用户 {current_user.id} 的新策略: {strategy_profile.preferred_style}")
            return jsonify({
                'success': True,
                'data': profile
            })

    except Exception as e:
        print(f"获取用户画像错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/strategy/update-profile', methods=['POST'])
@login_required
def update_strategy_profile():
    """更新用户画像（完成评估后调用）"""
    try:
        from personalized_healing import UserProfiler

        profiler = UserProfiler(current_user.id)
        profile = profiler.generate_profile()

        # 保存或更新到数据库
        strategy_profile = UserStrategyProfile.query.filter_by(user_id=current_user.id).first()

        if not strategy_profile:
            strategy_profile = UserStrategyProfile(user_id=current_user.id)

        strategy_profile.depression_level = profile['depression_level'].get('level', 'unknown')
        strategy_profile.trend_status = profile['trend'].get('status', 'new_user')
        strategy_profile.preferred_style = profile.get('recommended_style', 'guidance')
        strategy_profile.set_profile(profile)

        db.session.add(strategy_profile)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': profile
        })
    except Exception as e:
        db.session.rollback()
        print(f"更新用户画像错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/strategy/set-style', methods=['POST'])
@login_required
def set_conversation_style():
    """用户手动设置对话风格"""
    try:
        data = request.json
        style_id = data.get('style_id')

        if not style_id:
            return jsonify({'error': '缺少 style_id 参数'}), 400

        # 验证 style_id 是否有效
        valid_styles = ['empathetic', 'guidance', 'solution_focused', 'auto']
        if style_id not in valid_styles:
            return jsonify({'error': f'无效的 style_id，必须是: {", ".join(valid_styles)}'}), 400

        # 获取或创建用户策略画像
        strategy_profile = UserStrategyProfile.query.filter_by(user_id=current_user.id).first()

        if not strategy_profile:
            strategy_profile = UserStrategyProfile(user_id=current_user.id)
            db.session.add(strategy_profile)

        # 保存用户选择
        if style_id == 'auto':
            # 自动模式：根据系统推荐
            try:
                from personalized_healing import UserProfiler
                profiler = UserProfiler(current_user.id)
                profile = profiler.generate_profile()
                recommended_style = profile.get('recommended_style', 'guidance')

                strategy_profile.preferred_style = recommended_style
                strategy_profile.depression_level = profile['depression_level'].get('level', 'unknown')
                strategy_profile.trend_status = profile['trend'].get('status', 'new_user')
                strategy_profile.set_profile(profile)

                style_name = '自动推荐'
            except Exception as e:
                print(f"生成自动推荐失败: {e}")
                strategy_profile.preferred_style = 'guidance'
                style_name = '自动推荐'
        else:
            # 手动选择特定风格
            strategy_profile.preferred_style = style_id

            # 更新 profile JSON
            try:
                profile = strategy_profile.get_profile()
                if not profile:
                    profile = {}
                profile['manual_style_override'] = style_id
                profile['manual_override_time'] = datetime.now().isoformat()
                strategy_profile.set_profile(profile)
            except Exception as e:
                print(f"更新 profile 失败: {e}")

            # 风格名称映射
            style_names = {
                'empathetic': '共情型',
                'guidance': '指导型',
                'solution_focused': '解决型'
            }
            style_name = style_names.get(style_id, style_id)

        db.session.commit()

        print(f"✓ 用户 {current_user.id} 切换策略到: {style_id} ({style_name})")

        return jsonify({
            'success': True,
            'style_id': style_id,
            'style_name': style_name,
            'message': f'✓ 已切换到 {style_name}'
        })
    except Exception as e:
        db.session.rollback()
        print(f"设置对话风格错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/strategy/styles')
@login_required
def get_available_styles():
    """获取所有可用的对话风格"""
    try:
        from personalized_healing import UserProfile

        styles = []
        for style_id, style_info in UserProfile.CONVERSATION_STYLES.items():
            styles.append({
                'id': style_id,
                'name': style_info['name'],
                'description': style_info['description']
            })

        # 添加自动模式
        styles.insert(0, {
            'id': 'auto',
            'name': '自动推荐',
            'description': '根据你的评估结果自动选择最适合的对话风格'
        })

        return jsonify({
            'success': True,
            'styles': styles
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/strategy')
@login_required
def strategy_page():
    """策略管理页面"""
    return render_template('strategy_management.html')


# ==================== 主程序 ====================

if __name__ == "__main__":
    import sys

    # 初始化数据库
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

    # 初始化模型
    initialize_models()

    # 启动Flask应用
    print("\n🚀 启动服务器: http://127.0.0.1:5000")
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,  # 关闭debug模式避免编码问题
        use_reloader=False
    )
