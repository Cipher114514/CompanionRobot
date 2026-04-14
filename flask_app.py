"""
元气充能陪伴平台 - Flask版本
精简版：移除量表功能，简化对话系统
支持患者和心理咨询师两种角色
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import os
import csv
import io
import json

# 导入后端模块
from mindchat_dialogue import IntegratedMindChatSystem
from whisper_asr import WhisperASRManager
from voice_module import VoiceTTS

# 导入语音情绪识别模块（使用轻量级版本）
from voice_emotion_lightweight import init_lightweight_voice_emotion_recognizer

# 导入危机检测模块
from crisis_detection import CrisisDetector, CrisisResponder, CrisisStorage

# 导入模块化报告生成器
from modular_report_library import ModularReportGenerator

# 导入优化提示词生成器
from optimized_prompt_generator import (
    generate_prompt_with_memory,
    save_message_to_memory
)

# 导入统一配置
from config import (
    AppConfig, ModelConfig, VoiceConfig,
    ReportConfig, CrisisConfig, MediaConfig, PromptConfig,
    PerformanceConfig, LoggingConfig, PrivacyConfig, FeatureFlags,
    validate_config, create_missing_directories
)

# 导入数据库模型
from models import db, User, ChatMessage, SentimentAnalysis, ConversationFeedback, init_db

app = Flask(__name__)

# 配置
app.config.update(
    SECRET_KEY=AppConfig.SECRET_KEY,
    SQLALCHEMY_DATABASE_URI=AppConfig.SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=AppConfig.SQLALCHEMY_TRACK_MODIFICATIONS,
    PERMANENT_SESSION_LIFETIME=timedelta(days=AppConfig.PERMANENT_SESSION_LIFETIME_DAYS),
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
ser_system = None  # 语音情绪识别系统
crisis_detector = None
crisis_responder = None
crisis_storage = None
modular_report_generator = None  # 模块化报告生成器

# 创建静态音频目录（使用统一配置）
AUDIO_DIR = VoiceConfig.AUDIO_DIR
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login用户加载函数"""
    return User.query.get(int(user_id))


def calculate_age(birth_date):
    """计算年龄（基于出生日期）"""
    if birth_date is None:
        return None

    today = date.today()
    age = today.year - birth_date.year

    # 如果今年还没过生日，年龄减1
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age


def get_report_level(user):
    """
    根据用户年龄确定报告级别

    Args:
        user: User对象

    Returns:
        报告级别字符串: "none", "child", "teen", "adult"
    """
    if not user or not user.birth_date:
        return "adult"  # 默认成年人级别

    age = calculate_age(user.birth_date)

    if age is None:
        return "adult"

    # 根据年龄确定报告级别（基于认知发展理论）
    if age < ReportConfig.MIN_REPORT_AGE_CHILD:
        return "none"  # 不展示报告
    elif age < ReportConfig.MIN_REPORT_AGE_TEEN:
        return "child"  # 儿童简化报告
    elif age < ReportConfig.MIN_REPORT_AGE_ADULT:
        return "teen"   # 青少年适配报告
    else:
        return "adult"  # 成人完整报告


def initialize_models():
    """初始化所有模型"""
    global mindchat_system, asr_system, sentiment_pipeline, tts_system, multimodal_analyzer, ser_system
    global crisis_detector, crisis_responder, crisis_storage, modular_report_generator

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

    # 5. 语音情绪识别 (SER) - 基于音频特征的轻量级模型
    if VoiceConfig.ENABLE_VOICE_EMOTION:
        try:
            ser_system = init_lightweight_voice_emotion_recognizer()
            if ser_system and ser_system.loaded:
                print("[OK] 语音情绪识别系统加载成功 (轻量级特征模型)")
            else:
                print("[WARNING] 语音情绪识别加载失败，将使用基于规则的分析")
                ser_system = None
        except Exception as e:
            print(f"[ERROR] 语音情绪识别加载失败: {e}")
            ser_system = None

    # 6. 多模态情绪分析
    try:
        from multimodal_sentiment import create_multimodal_analyzer
        multimodal_analyzer = create_multimodal_analyzer(use_adaptive_weights=True)
        print("[OK] 多模态情绪分析系统加载成功（动态权重融合已启用）")
    except Exception as e:
        print(f"[ERROR] 多模态情绪分析加载失败: {e}")
        multimodal_analyzer = None

    # 7. 危机检测与干预系统
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

    # 8. 模块化报告生成器
    try:
        modular_report_generator = ModularReportGenerator()
        print("[OK] 模块化报告生成器加载成功")
        print(f"     - 可用模块数量: {len(modular_report_generator.modules)}")
    except Exception as e:
        print(f"[ERROR] 模块化报告生成器加载失败: {e}")
        import traceback
        traceback.print_exc()
        modular_report_generator = None

    print("=" * 60)
    print("初始化完成！")
    print("=" * 60)


def analyze_sentiment(text):
    """分析文本情绪，优先检测危机关键词"""
    # 危机关键词优先级检查（在ML模型之前）
    crisis_keywords = {
        'high': [
            "自杀", "自尽", "轻生", "不想活了", "结束生命", "去死", "活够了",
            "割腕", "跳楼", "吃药", "上吊", "了结", "解脱", "永别", "再见了"
        ],
        'medium': [
            "伤害自己", "撑不下去", "太累了", "好痛苦", "受不了", "崩溃",
            "绝望", "没希望", "没意义", "活着干嘛", "不如死了", "想消失"
        ],
        'low': [
            "难过", "伤心", "委屈", "孤独", "无助", "迷茫", "焦虑", "害怕",
            "烦躁", "沮丧", "失落", "疲惫", "空虚", "无力", "好累", "心累",
            "想哭", "难受", "不舒服", "不对劲", "状态差", "心情不好", "痛苦"
        ]
    }

    # 检查high级别关键词（最危险）
    for keyword in crisis_keywords['high']:
        if keyword in text:
            print(f"[情绪分析] 检测到高危关键词 '{keyword}'，强制为负面情绪")
            return {"emotion": "negative", "confidence": 1.0, "detected_by": "crisis_keyword_high"}

    # 检查medium级别关键词
    for keyword in crisis_keywords['medium']:
        if keyword in text:
            print(f"[情绪分析] 检测到中危关键词 '{keyword}'，强制为负面情绪")
            return {"emotion": "negative", "confidence": 0.8, "detected_by": "crisis_keyword_medium"}

    # 检查low级别关键词（轻微负面）
    for keyword in crisis_keywords['low']:
        if keyword in text:
            print(f"[情绪分析] 检测到低危关键词 '{keyword}'，倾向负面情绪")
            # 对于低危关键词，给ML模型一个参考，但不完全覆盖
            # 如果ML模型返回neutral，我们覆盖为negative
            if sentiment_pipeline is None:
                return {"emotion": "negative", "confidence": 0.6, "detected_by": "crisis_keyword_low"}

    # 使用ML模型分析（如果没有检测到高危/中危关键词）
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

        # 如果检测到低危关键词，且ML模型返回neutral，覆盖为negative
        for keyword in crisis_keywords['low']:
            if keyword in text and emotion == 'neutral':
                print(f"[情绪分析] 低危关键词 '{keyword}' 覆盖ML的neutral判断")
                return {"emotion": "negative", "confidence": 0.6, "detected_by": "crisis_keyword_low_override"}

        return {"emotion": emotion, "confidence": confidence, "detected_by": "ml_model"}
    except Exception as e:
        print(f"情绪分析错误: {e}")
        return {"emotion": "neutral", "confidence": 0.0}


def voice_features_to_emotion(audio_features):
    """
    将语音特征转换为情绪标签

    Args:
        audio_features: 语音特征字典 {
            'pitch_mean': float,
            'pitch_std': float,
            'tempo': float,
            'energy': float,
            'shimmer': float
        }

    Returns:
        情绪字典 {"emotion": "positive/negative/neutral", "confidence": float}
    """
    if not audio_features or not audio_features.get('success', False):
        return {"emotion": "neutral", "confidence": 0.0}

    features = audio_features

    # 计算情绪得分
    negative_score = 0.0
    positive_score = 0.0

    # 1. 低音高 → 负面情绪（抑郁倾向）
    pitch_mean = features.get('pitch_mean', 0)
    if pitch_mean > 0:
        if pitch_mean < 120:
            negative_score += 0.4
        elif pitch_mean < 150:
            negative_score += 0.2

    # 2. 低能量 → 负面情绪
    energy = features.get('energy', 0)
    if energy < 0.05:
        negative_score += 0.4
    elif energy < 0.1:
        negative_score += 0.2
    elif energy > 0.2:
        # 高能量可能是正面情绪（兴奋）
        positive_score += 0.2

    # 3. 高语速 → 中性/焦虑倾向（不算强烈的负面）
    tempo = features.get('tempo', 0)
    if tempo > 6.0:
        # 语速过快可能是焦虑，但不算negative
        pass
    elif 3.0 <= tempo <= 5.0:
        # 正常语速，略微偏向正面
        positive_score += 0.1

    # 4. 音高变化大 → 情绪波动
    pitch_std = features.get('pitch_std', 0)
    shimmer = features.get('shimmer', 0)

    # 适度的音高变化可能是正面（表达丰富）
    if 10 < pitch_std < 30:
        positive_score += 0.2
    # 过大的变化可能是情绪不稳定
    elif pitch_std > 50:
        negative_score += 0.2

    if 0.05 < shimmer < 0.15:
        positive_score += 0.1
    elif shimmer > 0.3:
        negative_score += 0.2

    # 判定情绪
    confidence = max(negative_score, positive_score, 0.3)  # 最低置信度0.3

    if negative_score > positive_score and negative_score > 0.3:
        return {"emotion": "negative", "confidence": round(confidence, 3)}
    elif positive_score > negative_score and positive_score > 0.3:
        return {"emotion": "positive", "confidence": round(confidence, 3)}
    else:
        return {"emotion": "neutral", "confidence": round(confidence, 3)}


def fuse_emotions(text_emotion, voice_emotion, enable_voice=True):
    """
    融合文字情绪和语音情绪

    Args:
        text_emotion: 文字情绪分析结果 {"emotion": str, "confidence": float}
        voice_emotion: 语音情绪分析结果 {"emotion": str, "confidence": float}
        enable_voice: 是否启用语音情绪分析

    Returns:
        融合后的情绪 {"emotion": str, "confidence": float, "method": str}
    """
    # 如果未启用语音情绪分析，直接返回文字情绪
    if not enable_voice or voice_emotion.get("confidence", 0) < 0.2:
        return {
            "emotion": text_emotion.get("emotion", "neutral"),
            "confidence": text_emotion.get("confidence", 0.0),
            "method": "text_only"
        }

    # 情绪到数值的映射
    emotion_scores = {
        "positive": 1.0,
        "neutral": 0.5,
        "negative": 0.0
    }

    text_score = emotion_scores.get(text_emotion.get("emotion", "neutral"), 0.5)
    voice_score = emotion_scores.get(voice_emotion.get("emotion", "neutral"), 0.5)

    # 文字情绪和语音情绪的置信度
    text_conf = text_emotion.get("confidence", 0.5)
    voice_conf = voice_emotion.get("confidence", 0.5)

    # 加权融合
    fused_score = (
        text_score * VoiceConfig.TEXT_EMOTION_WEIGHT * text_conf +
        voice_score * VoiceConfig.VOICE_EMOTION_WEIGHT * voice_conf
    ) / (VoiceConfig.TEXT_EMOTION_WEIGHT * text_conf + VoiceConfig.VOICE_EMOTION_WEIGHT * voice_conf)

    # 将分数转换回情绪标签
    if fused_score >= 0.7:
        fused_emotion = "positive"
    elif fused_score <= 0.3:
        fused_emotion = "negative"
    else:
        fused_emotion = "neutral"

    # 融合置信度（加权平均）
    fused_confidence = (
        text_conf * VoiceConfig.TEXT_EMOTION_WEIGHT +
        voice_conf * VoiceConfig.VOICE_EMOTION_WEIGHT
    )

    return {
        "emotion": fused_emotion,
        "confidence": round(fused_confidence, 3),
        "method": "multimodal_fusion",
        "details": {
            "text_emotion": text_emotion.get("emotion"),
            "voice_emotion": voice_emotion.get("emotion"),
            "text_weight": VoiceConfig.TEXT_EMOTION_WEIGHT,
            "voice_weight": VoiceConfig.VOICE_EMOTION_WEIGHT
        }
    }


# ==================== 路由 ====================

# ==================== 认证相关路由 ====================

@app.route('/register')
def register_page():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/login')
def login_page():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/')
def home():
    """首页 - 根据用户角色重定向"""
    if not current_user.is_authenticated:
        return redirect(url_for('login_page'))

    # 根据角色跳转不同页面
    if current_user.is_counselor():
        return redirect(url_for('counselor_dashboard'))
    else:
        return redirect(url_for('chat_page'))


@app.route('/chat')
@login_required
def chat_page():
    """疗愈机器人页面（仅患者）"""
    if current_user.is_counselor():
        return redirect(url_for('counselor_dashboard'))

    # 计算年龄和报告级别
    age = calculate_age(current_user.birth_date)
    report_level = get_report_level(current_user)
    can_view_report = report_level != "none"

    return render_template('chat.html',
                          age=age,
                          report_level=report_level,
                          can_view_report=can_view_report)


@app.route('/report')
@login_required
def report():
    """报告页面（仅患者）"""
    if current_user.is_counselor():
        return redirect(url_for('counselor_dashboard'))

    # 检查用户是否有权查看报告
    report_level = get_report_level(current_user)
    if report_level == "none":
        return redirect(url_for('chat_page'))

    age = calculate_age(current_user.birth_date)

    return render_template('report.html',
                          age=age,
                          report_level=report_level)


@app.route('/profile')
@login_required
def profile_page():
    """个人中心页面（仅患者）"""
    if current_user.is_counselor():
        return redirect(url_for('counselor_dashboard'))

    # 计算年龄和报告级别
    age = calculate_age(current_user.birth_date)
    report_level = get_report_level(current_user)
    can_view_report = report_level != "none"

    return render_template('profile.html',
                          age=age,
                          report_level=report_level,
                          can_view_report=can_view_report)


@app.route('/counselor')
@login_required
def counselor_dashboard():
    """心理咨询师仪表盘（仅咨询师）"""
    if not current_user.is_counselor():
        return redirect(url_for('chat_page'))
    return render_template('counselor_dashboard.html')


@app.route('/favicon.ico')
def favicon():
    """返回空 favicon 避免 404 错误"""
    from flask import Response
    return Response('', mimetype='image/x-icon')


@app.route('/api/debug/status')
@login_required
def debug_status():
    """调试端点：检查全局变量状态"""
    return jsonify({
        "modular_report_generator": modular_report_generator is not None,
        "modular_report_generator_type": str(type(modular_report_generator)) if modular_report_generator else None,
        "mindchat_system": mindchat_system is not None,
        "crisis_detector": crisis_detector is not None
    })


# ==================== 认证相关 API ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册API"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', 'patient').strip()
        birth_date_str = data.get('birth_date', '').strip()

        # 验证输入
        if not username or not email or not password or not role:
            return jsonify({"error": "请填写所有必填字段"}), 400

        if role not in ['patient', 'counselor']:
            return jsonify({"error": "无效的用户角色"}), 400

        if len(username) < 3 or len(username) > 20:
            return jsonify({"error": "用户名长度必须在3-20个字符之间"}), 400

        if len(password) < 6:
            return jsonify({"error": "密码长度至少为6个字符"}), 400

        # 患者必须提供出生日期
        if role == 'patient' and not birth_date_str:
            return jsonify({"error": "请填写出生日期"}), 400

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "用户名已存在"}), 400

        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "邮箱已被注册"}), 400

        # 创建新用户
        user = User(username=username, email=email, role=role)
        user.set_password(password)

        # 解析出生日期（仅患者）
        if role == 'patient' and birth_date_str:
            try:
                user.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "出生日期格式错误，应为 YYYY-MM-DD"}), 400

        db.session.add(user)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "注册成功！请登录",
            "role": role
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


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """用户登出（支持GET和POST）"""
    try:
        logout_user()
        if request.method == 'POST':
            return jsonify({"success": True, "message": "已退出登录"})
        else:
            return redirect(url_for('login_page'))
    except Exception as e:
        if request.method == 'POST':
            return jsonify({"error": "退出失败"}), 500
        else:
            return redirect(url_for('login_page'))


@app.route('/api/auth/logout', methods=['GET', 'POST'])
def logout_api():
    """用户登出API（保持兼容）"""
    try:
        logout_user()
        if request.method == 'POST':
            return jsonify({"success": True, "message": "已退出登录"})
        else:
            return redirect('/')
    except Exception as e:
        if request.method == 'POST':
            return jsonify({"error": "退出失败"}), 500
        else:
            return redirect('/')


@app.route('/api/user/info')
@login_required
def get_user_info():
    """获取当前用户信息"""
    return jsonify(current_user.to_dict())


@app.route('/api/profile', methods=['GET'])
@login_required
def get_user_profile():
    """获取用户画像（仅患者）"""
    if current_user.is_counselor():
        return jsonify({"error": "心理咨询师无此功能"}), 403

    try:
        from user_profile import UserProfile
        user_profile = UserProfile.load_from_database(current_user)
        return jsonify({
            'success': True,
            'profile': user_profile.to_dict(),
            'summary': user_profile.get_summary()
        })
    except Exception as e:
        print(f"获取用户画像错误: {e}")
        return jsonify({"error": "获取用户画像失败"}), 500


@app.route('/api/profile', methods=['PUT'])
@login_required
def update_user_profile():
    """更新用户画像（仅患者）"""
    if current_user.is_counselor():
        return jsonify({"error": "心理咨询师无此功能"}), 403

    try:
        data = request.json
        field = data.get('field')
        value = data.get('value')

        if not field:
            return jsonify({"error": "缺少字段名"}), 400

        # 验证字段
        valid_fields = ['name', 'age', 'job', 'hobbies', 'concerns', 'preferences']
        if field not in valid_fields:
            return jsonify({"error": "无效的字段名"}), 400

        # 更新字段
        current_user.update_profile_field(field, value)
        db.session.commit()

        # 返回更新后的画像
        from user_profile import UserProfile
        user_profile = UserProfile.load_from_database(current_user)

        return jsonify({
            'success': True,
            'message': f'已更新{field}',
            'profile': user_profile.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        print(f"更新用户画像错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "更新用户画像失败"}), 500


@app.route('/api/profile/reset', methods=['POST'])
@login_required
def reset_user_profile():
    """清空用户画像（仅患者）"""
    if current_user.is_counselor():
        return jsonify({"error": "心理咨询师无此功能"}), 403

    try:
        # 清空画像字段
        current_user.profile_name = None
        current_user.profile_age = None
        current_user.profile_job = None
        current_user.profile_hobbies = None
        current_user.profile_concerns = None
        current_user.profile_preferences = None
        current_user.profile_last_updated = None

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '用户画像已清空'
        })
    except Exception as e:
        db.session.rollback()
        print(f"清空用户画像错误: {e}")
        return jsonify({"error": "清空用户画像失败"}), 500


# ==================== 患者相关 API ====================

@app.route('/api/user/statistics')
@login_required
def get_user_statistics():
    """获取用户统计信息（仅患者）"""
    if current_user.is_counselor():
        return jsonify({"error": "心理咨询师无此功能"}), 403

    try:
        # 获取对话总数
        total_chats = ChatMessage.query.filter_by(user_id=current_user.id).count()

        # 获取情绪统计
        from sqlalchemy import func
        emotion_stats = db.session.query(
            ChatMessage.emotion,
            func.count(ChatMessage.id)
        ).filter_by(
            user_id=current_user.id
        ).group_by(
            ChatMessage.emotion
        ).all()

        emotion_counts = {e: 0 for e in ['positive', 'negative', 'neutral']}
        for emotion, count in emotion_stats:
            if emotion in emotion_counts:
                emotion_counts[emotion] = count

        # 最近一次对话时间
        latest_chat = ChatMessage.query.filter_by(user_id=current_user.id)\
            .order_by(ChatMessage.created_at.desc())\
            .first()

        latest_date = latest_chat.created_at.isoformat() if latest_chat else None

        return jsonify({
            'total_chats': total_chats,
            'emotion_counts': emotion_counts,
            'latest_date': latest_date
        })

    except Exception as e:
        print(f"获取统计信息错误: {e}")
        return jsonify({"error": "获取统计信息失败"}), 500


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
    """删除单条聊天消息"""
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
            'error': '删除消息失败'
        }), 500


@app.route('/api/user/chat-messages/clear', methods=['DELETE'])
@login_required
def clear_all_chat_messages():
    """清空当前用户的所有聊天消息"""
    try:
        # 删除当前用户的所有聊天消息
        ChatMessage.query.filter_by(user_id=current_user.id).delete()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '清空成功'
        })

    except Exception as e:
        db.session.rollback()
        print(f"清空消息错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': '清空消息失败'
        }), 500


@app.route('/api/user/trend-data')
@login_required
def get_user_trend_data():
    """获取用户历史趋势数据"""
    if current_user.is_counselor():
        return jsonify({"error": "心理咨询师无此功能"}), 403

    try:
        # 获取聊天数据
        chat_messages = ChatMessage.query.filter_by(user_id=current_user.id)\
            .order_by(ChatMessage.created_at.asc())\
            .all()

        # 分析聊天情绪趋势
        chat_emotion_data = []
        emotion_counts = {'positive': 0, 'negative': 0, 'neutral': 0}

        valid_emotions = {'positive', 'negative', 'neutral'}

        for msg in chat_messages:
            emotion = msg.emotion if msg.emotion in valid_emotions else 'neutral'

            chat_emotion_data.append({
                'date': msg.created_at.isoformat(),
                'emotion': emotion,
                'confidence': msg.confidence
            })
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        # 计算最近7天的情绪分布
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_chats = [m for m in chat_messages if m.created_at >= week_ago]
        recent_emotion_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for msg in recent_chats:
            emotion = msg.emotion if msg.emotion in valid_emotions else 'neutral'
            recent_emotion_counts[emotion] = recent_emotion_counts.get(emotion, 0) + 1

        return jsonify({
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


@app.route('/api/report/generate')
@login_required
def generate_age_adaptive_report():
    """生成模块化情绪报告API (Layer 1: 数据概览 + 模块推荐)"""
    print(f"\n[DEBUG] /api/report/generate 被调用")
    print(f"[DEBUG] current_user.id: {current_user.id}")
    print(f"[DEBUG] current_user.birth_date: {current_user.birth_date}")

    if current_user.is_counselor():
        return jsonify({"error": "咨询师无需使用此功能"}), 403

    try:
        # 检查用户是否有权查看报告
        report_level = get_report_level(current_user)
        print(f"[DEBUG] report_level: {report_level}")

        if report_level == "none":
            return jsonify({"error": "您还未达到查看报告的年龄要求"}), 403

        # 检查模块化报告生成器是否可用
        print(f"[DEBUG] modular_report_generator is None: {modular_report_generator is None}")
        if modular_report_generator is None:
            print("[ERROR] modular_report_generator is None!")
            return jsonify({"error": "报告生成器未初始化"}), 500

        # 计算年龄
        age = calculate_age(current_user.birth_date)
        print(f"[DEBUG] calculated age: {age}")

        # 生成Layer 1报告（数据概览 + 模块推荐）
        print(f"[DEBUG] 开始生成报告...")
        report = modular_report_generator.generate_layer1_report(
            user_id=current_user.id,
            age=age,
            report_level=report_level
        )
        print(f"[DEBUG] 报告生成成功")

        return jsonify({
            "success": True,
            "report": report
        })

    except Exception as e:
        print(f"[ERROR] 生成报告错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"生成报告失败: {str(e)}"}), 500


@app.route('/api/report/module/<module_name>')
@login_required
def get_report_module_detail(module_name):
    """获取指定模块的详细内容 (Layer 2)"""
    if current_user.is_counselor():
        return jsonify({"error": "咨询师无需使用此功能"}), 403

    try:
        # 检查用户是否有权查看报告
        report_level = get_report_level(current_user)
        if report_level == "none":
            return jsonify({"error": "您还未达到查看报告的年龄要求"}), 403

        # 检查模块化报告生成器是否可用
        if modular_report_generator is None:
            return jsonify({"error": "报告生成器未初始化"}), 500

        # 计算年龄
        age = calculate_age(current_user.birth_date)

        # 获取模块详情
        module_detail = modular_report_generator.get_layer2_module(
            module_name=module_name,
            age=age,
            report_level=report_level
        )

        if module_detail is None:
            return jsonify({"error": f"模块 '{module_name}' 不存在"}), 404

        return jsonify({
            "success": True,
            "module": module_detail
        })

    except Exception as e:
        print(f"获取模块详情错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "获取模块详情失败"}), 500


@app.route('/api/profile/export')
@login_required
def export_profile_data():
    """导出用户数据为CSV文件"""
    if current_user.is_counselor():
        return jsonify({"error": "心理咨询师无此功能"}), 403

    try:
        # 创建内存中的CSV文件
        output = io.StringIO()

        # 获取所有对话记录
        chat_messages = ChatMessage.query.filter_by(user_id=current_user.id)\
            .order_by(ChatMessage.created_at.desc())\
            .all()

        # 写入CSV
        writer = csv.writer(output)

        # 写入对话记录
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


# ==================== 心理咨询师相关 API ====================

@app.route('/api/counselor/patients')
@login_required
def get_all_patients():
    """获取所有患者列表（仅咨询师）"""
    if not current_user.is_counselor():
        return jsonify({"error": "无权访问"}), 403

    try:
        # 获取所有患者
        patients = User.query.filter_by(role='patient').order_by(User.created_at.desc()).all()

        patient_list = []
        for patient in patients:
            # 获取患者的对话统计
            chat_count = ChatMessage.query.filter_by(user_id=patient.id).count()

            # 获取最近的对话时间
            latest_chat = ChatMessage.query.filter_by(user_id=patient.id)\
                .order_by(ChatMessage.created_at.desc())\
                .first()

            # 计算年龄
            age = None
            if patient.birth_date:
                today = date.today()
                age = today.year - patient.birth_date.year - (
                    (today.month, today.day) < (patient.birth_date.month, patient.birth_date.day)
                )

            patient_list.append({
                'id': patient.id,
                'username': patient.username,
                'email': patient.email,
                'birth_date': patient.birth_date.isoformat() if patient.birth_date else None,
                'age': age,
                'created_at': patient.created_at.strftime('%Y-%m-%d') if patient.created_at else None,
                'last_login': patient.last_login.strftime('%Y-%m-%d %H:%M:%S') if patient.last_login else None,
                'chat_count': chat_count,
                'latest_chat_date': latest_chat.created_at.strftime('%Y-%m-%d %H:%M:%S') if latest_chat else None
            })

        return jsonify({
            'success': True,
            'patients': patient_list,
            'total': len(patient_list)
        })

    except Exception as e:
        print(f"获取患者列表错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "获取患者列表失败"}), 500


@app.route('/api/counselor/patient/<int:patient_id>')
@login_required
def get_patient_detail(patient_id):
    """获取患者详细信息（仅咨询师）"""
    if not current_user.is_counselor():
        return jsonify({"error": "无权访问"}), 403

    try:
        patient = User.query.filter_by(id=patient_id, role='patient').first()
        if not patient:
            return jsonify({"error": "患者不存在"}), 404

        # 获取患者的对话记录
        chat_messages = ChatMessage.query.filter_by(user_id=patient_id)\
            .order_by(ChatMessage.created_at.desc())\
            .limit(100)\
            .all()

        # 获取情绪统计
        from sqlalchemy import func
        emotion_stats = db.session.query(
            ChatMessage.emotion,
            func.count(ChatMessage.id)
        ).filter_by(
            user_id=patient_id
        ).group_by(
            ChatMessage.emotion
        ).all()

        emotion_counts = {e: 0 for e in ['positive', 'negative', 'neutral']}
        for emotion, count in emotion_stats:
            if emotion in emotion_counts:
                emotion_counts[emotion] = count

        # 计算年龄
        age = None
        if patient.birth_date:
            today = date.today()
            age = today.year - patient.birth_date.year - (
                (today.month, today.day) < (patient.birth_date.month, patient.birth_date.day)
            )

        # 获取危机干预记录
        crisis_count = ChatMessage.query.filter_by(
            user_id=patient_id,
            is_crisis_response=True
        ).count()

        return jsonify({
            'success': True,
            'patient': {
                'id': patient.id,
                'username': patient.username,
                'email': patient.email,
                'birth_date': patient.birth_date.isoformat() if patient.birth_date else None,
                'age': age,
                'created_at': patient.created_at.isoformat() if patient.created_at else None,
                'last_login': patient.last_login.isoformat() if patient.last_login else None,
                'chat_count': len(chat_messages),
                'emotion_counts': emotion_counts,
                'crisis_count': crisis_count
            },
            'recent_chats': [{
                'id': msg.id,
                'user_message': msg.user_message,
                'bot_response': msg.bot_response,
                'emotion': msg.emotion,
                'is_crisis_response': msg.is_crisis_response,
                'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S') if msg.created_at else None
            } for msg in chat_messages]
        })

    except Exception as e:
        print(f"获取患者详情错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "获取患者详情失败"}), 500


# 固定的 system prompt


@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """处理聊天请求（仅患者）"""
    if current_user.is_counselor():
        return jsonify({"error": "心理咨询师不能使用对话功能"}), 403

    data = request.json
    message = data.get('message', '').strip()
    voice_emotion_data = data.get('voice_emotion')  # 接收语音情绪数据

    # 验证消息不为空且有实际内容
    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    # 检查消息长度（防止极短无效输入）
    if len(message) < 2:
        return jsonify({"error": "消息内容太短，请重新输入"}), 400

    try:
        # ========== 用户画像处理 ==========
        # 加载用户画像
        from user_profile import UserProfile
        user_profile = UserProfile.load_from_database(current_user)

        # 从消息中提取新的画像信息（持续学习）
        updated, updated_fields = user_profile.extract_from_message(message)
        if updated:
            print(f"[用户画像] 从消息中提取到新信息: {updated_fields}")
            # 保存到数据库
            user_profile.save_to_database()

        # 1. 分析文字情绪
        text_emotion = analyze_sentiment(message)

        # 2. 如果提供了语音情绪，进行融合分析
        if voice_emotion_data and VoiceConfig.ENABLE_VOICE_EMOTION:
            emotion_data = fuse_emotions(text_emotion, voice_emotion_data, enable_voice=True)
            print(f"[多模态情绪融合] 文字: {text_emotion['emotion']}, 语音: {voice_emotion_data.get('emotion')}, 融合: {emotion_data['emotion']}")
        else:
            emotion_data = text_emotion
            emotion_data["method"] = "text_only"

        # 2. 危机检测
        crisis_detected = False
        crisis_level = 0
        crisis_response_data = None

        if crisis_detector:
            try:
                # 执行危机检测（使用融合后的情绪）
                voice_emotion_for_crisis = None
                if voice_emotion_data and VoiceConfig.ENABLE_VOICE_EMOTION:
                    voice_emotion_for_crisis = voice_emotion_data

                detection_result = crisis_detector.detect(
                    user_input=message,
                    user_id=current_user.id,
                    voice_emotion=voice_emotion_for_crisis,
                    scale_scores=None
                )

                # 如果检测到危机
                if detection_result.is_crisis:
                    crisis_detected = True
                    crisis_level = detection_result.level

                    print(f"[危机检测] 用户 {current_user.id}: 检测到危机等级 {crisis_level}")

                    # 记录到危机事件数据库
                    if crisis_storage:
                        try:
                            crisis_storage.log_event(detection_result, current_user.id)
                        except Exception as e:
                            print(f"记录危机事件失败: {e}")

                    # 生成危机干预回复
                    if crisis_responder:
                        try:
                            intervention = crisis_responder.generate(
                                level=detection_result.level,
                                keywords=detection_result.keywords,
                                emotion=emotion_data.get("emotion"),
                                user_input=message,
                                user_context={"user_id": current_user.id}
                            )

                            print(f"[危机干预] 生成成功: should_cover={intervention.should_cover}, is_ai_generated={intervention.is_ai_generated}")
                            print(f"[危机干预] 回复内容: {intervention.content[:100] if intervention.content else 'None'}...")

                            crisis_response_data = intervention

                            # 如果需要覆盖正常回复（2级及以上）
                            if intervention.should_cover:
                                print(f"[危机干预] 使用干预回复覆盖正常回复")
                                response = intervention.content

                                # 验证response
                                if not response or len(response) < 10:
                                    print(f"[危机干预] 警告：回复异常，使用备用模板")
                                    response = "我很关心你的状态。请考虑联系专业帮助。"

                                # 保存聊天记录
                                chat_message = ChatMessage(
                                    user_id=current_user.id,
                                    user_message=message,
                                    bot_response=response,
                                    emotion=emotion_data["emotion"],
                                    confidence=emotion_data["confidence"],
                                    is_crisis_response=True
                                )
                                db.session.add(chat_message)
                                db.session.commit()

                                print(f"[危机干预] 即将return，不再执行正常对话")
                                return jsonify({
                                    "success": True,  # ← 添加success字段，前端依赖此字段判断
                                    "response": response,
                                    "emotion": emotion_data,
                                    "audio_path": None,
                                    "crisis_detected": True,
                                    "crisis_level": crisis_level,
                                    "crisis_intervention": True
                                })
                            else:
                                print(f"[危机干预] should_cover=False，继续正常对话")
                        except Exception as e:
                            print(f"[危机干预] 生成失败: {e}")
                            import traceback
                            traceback.print_exc()

            except Exception as e:
                print(f"危机检测失败: {e}")
                import traceback
                traceback.print_exc()

        # 3. 生成系统提示词
        conversation_id = f"user_{current_user.id}"  # 每个用户一个会话

        # 使用用户画像生成自适应系统提示词
        system_prompt = user_profile.get_adaptive_system_prompt(PromptConfig.FIXED_SYSTEM_PROMPT)

        # 生成回复
        result = mindchat_system.analyze_and_respond(message, system_prompt=system_prompt, user_id=current_user.id)

        if result.get("success"):
            response = result["response"]

            # 获取引导问题
            follow_up_questions = result.get("follow_up_questions", [])

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

            # 保存聊天记录到数据库
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

            # 准备返回数据
            response_data = {
                "success": True,
                "response": response if response else "我在听，请继续说。",
                "emotion": emotion_data["emotion"],
                "confidence": emotion_data["confidence"],
                "audio_path": audio_path,
                "chat_message_id": chat_message.id,
                "follow_up_questions": follow_up_questions
            }

            # 如果使用了融合情绪分析，返回详细信息
            if "method" in emotion_data:
                response_data["emotion_method"] = emotion_data["method"]
                if "details" in emotion_data:
                    response_data["emotion_details"] = emotion_data["details"]

            return jsonify(response_data)
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
                    "duration": features.get("duration", 0),
                    "success": features.get("success", False)
                }

                # 如果特征提取成功，分析语音情绪
                if features.get("success") and VoiceConfig.ENABLE_VOICE_EMOTION:
                    # 优先使用预训练模型
                    if ser_system and ser_system.loaded:
                        try:
                            voice_emotion_result = ser_system.predict(audio_path)
                            if voice_emotion_result.get("success"):
                                voice_emotion = {
                                    "emotion": voice_emotion_result["emotion"],
                                    "confidence": voice_emotion_result["confidence"],
                                    "method": "pretrained_model",
                                    "raw_emotion": voice_emotion_result.get("raw_emotion")
                                }
                                response_data["voice_emotion"] = voice_emotion
                                print(f"[ASR] 语音情绪分析 (预训练模型): {voice_emotion}")
                            else:
                                # 模型失败，使用规则方法
                                voice_emotion = voice_features_to_emotion(features)
                                voice_emotion["method"] = "rule_based"
                                response_data["voice_emotion"] = voice_emotion
                                print(f"[ASR] 语音情绪分析 (规则): {voice_emotion}")
                        except Exception as e:
                            print(f"[ERROR] SER模型预测失败: {e}，使用规则方法")
                            voice_emotion = voice_features_to_emotion(features)
                            voice_emotion["method"] = "rule_based"
                            response_data["voice_emotion"] = voice_emotion
                            print(f"[ASR] 语音情绪分析 (规则): {voice_emotion}")
                    else:
                        # 无SER模型，使用规则方法
                        voice_emotion = voice_features_to_emotion(features)
                        voice_emotion["method"] = "rule_based"
                        response_data["voice_emotion"] = voice_emotion
                        print(f"[ASR] 语音情绪分析 (规则): {voice_emotion}")

                # 打印心理健康评估信息
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
    """多模态情绪分析API"""
    if current_user.is_counselor():
        return jsonify({"error": "心理咨询师不能使用此功能"}), 403

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
    """提交对话反馈API - 用于RLHF轻量级实现"""
    if current_user.is_counselor():
        return jsonify({"error": "心理咨询师不能使用此功能"}), 403

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


# ==================== 心理咨询师仪表盘 API ====================

def calculate_user_status(patient):
    """计算用户状态"""
    from datetime import timedelta

    # 获取最近对话
    latest_chat = ChatMessage.query.filter_by(user_id=patient.id)\
        .order_by(ChatMessage.created_at.desc())\
        .first()

    if not latest_chat:
        return {"status": "inactive", "label": "未活跃", "color": "gray"}

    days_since = (datetime.now() - latest_chat.created_at).days

    # 检查是否有近期危机事件
    try:
        if crisis_storage:
            recent_crisis = crisis_storage.get_unhandled_events(user_id=patient.id)
            if recent_crisis:
                return {"status": "crisis", "label": "危机预警", "color": "red"}
    except:
        pass

    # 根据活跃度和情绪判断状态
    if days_since <= 1:
        return {"status": "active", "label": "活跃", "color": "green"}
    elif days_since <= 7:
        return {"status": "normal", "label": "正常", "color": "blue"}
    else:
        return {"status": "inactive", "label": "长期未活跃", "color": "orange"}


def get_patient_emotion_trend(patient_id, days=7):
    """获取患者情绪趋势"""
    from datetime import timedelta
    from sqlalchemy import func

    start_date = datetime.now() - timedelta(days=days)

    # 按天统计情绪
    emotions = db.session.query(
        func.date(ChatMessage.created_at).label('date'),
        ChatMessage.emotion,
        func.count(ChatMessage.id).label('count')
    ).filter(
        ChatMessage.user_id == patient_id,
        ChatMessage.created_at >= start_date
    ).group_by(
        func.date(ChatMessage.created_at),
        ChatMessage.emotion
    ).all()

    trend = {}
    for date, emotion, count in emotions:
        date_str = date.strftime('%Y-%m-%d')
        if date_str not in trend:
            trend[date_str] = {'positive': 0, 'negative': 0, 'neutral': 0}
        trend[date_str][emotion] = count

    return trend


@app.route('/api/counselor/dashboard/stats')
@login_required
def get_dashboard_stats():
    """获取仪表盘统计数据（仅咨询师）"""
    if not current_user.is_counselor():
        return jsonify({"error": "无权访问"}), 403

    try:
        from datetime import timedelta, date

        # 用户总数
        total_patients = User.query.filter_by(role='patient').count()

        # 今日活跃用户（24小时内有对话）
        yesterday = datetime.now() - timedelta(days=1)
        today_active = db.session.query(ChatMessage.user_id)\
            .filter(ChatMessage.created_at >= yesterday)\
            .distinct()\
            .count()

        # 危机预警用户
        crisis_count = 0
        try:
            if crisis_storage:
                crisis_events = crisis_storage.get_unhandled_events()
                # 获取唯一用户数
                crisis_users = set(event.user_id for event in crisis_events)
                crisis_count = len(crisis_users)
        except:
            pass

        # 本周新用户
        week_ago = datetime.now() - timedelta(days=7)
        new_week_patients = User.query.filter(
            User.role == 'patient',
            User.created_at >= week_ago
        ).count()

        return jsonify({
            'success': True,
            'stats': {
                'total_patients': total_patients,
                'today_active': today_active,
                'crisis_warning': crisis_count,
                'new_week_patients': new_week_patients
            }
        })

    except Exception as e:
        print(f"获取仪表盘统计错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "获取统计数据失败"}), 500


@app.route('/api/counselor/patients/enhanced')
@login_required
def get_all_patients_enhanced():
    """获取所有患者列表（增强版，含状态标签）"""
    if not current_user.is_counselor():
        return jsonify({"error": "无权访问"}), 403

    try:
        patients = User.query.filter_by(role='patient').order_by(User.created_at.desc()).all()

        patient_list = []
        for patient in patients:
            # 计算年龄
            age = None
            if patient.birth_date:
                today = date.today()
                age = today.year - patient.birth_date.year - (
                    (today.month, today.day) < (patient.birth_date.month, patient.birth_date.day)
                )

            # 获取最近对话
            latest_chat = ChatMessage.query.filter_by(user_id=patient.id)\
                .order_by(ChatMessage.created_at.desc())\
                .first()

            # 计算用户状态
            status_info = calculate_user_status(patient)

            # 获取对话总数
            chat_count = ChatMessage.query.filter_by(user_id=patient.id).count()

            # 获取最近情绪
            recent_emotion = None
            if latest_chat:
                recent_emotion = latest_chat.emotion

            patient_list.append({
                'id': patient.id,
                'username': patient.username,
                'email': patient.email,
                'age': age,
                'created_at': patient.created_at.strftime('%Y-%m-%d') if patient.created_at else None,
                'last_login': patient.last_login.strftime('%Y-%m-%d %H:%M') if patient.last_login else None,
                'chat_count': chat_count,
                'latest_chat_date': latest_chat.created_at.strftime('%Y-%m-%d %H:%M') if latest_chat else None,
                'status': status_info,
                'recent_emotion': recent_emotion
            })

        return jsonify({
            'success': True,
            'patients': patient_list,
            'total': len(patient_list)
        })

    except Exception as e:
        print(f"获取患者列表错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "获取患者列表失败"}), 500


@app.route('/api/counselor/patient/<int:patient_id>/emotion-trend')
@login_required
def get_patient_emotion_trend_api(patient_id):
    """获取患者情绪趋势"""
    if not current_user.is_counselor():
        return jsonify({"error": "无权访问"}), 403

    try:
        days = request.args.get('days', 7, type=int)
        trend = get_patient_emotion_trend(patient_id, days)

        return jsonify({
            'success': True,
            'trend': trend
        })

    except Exception as e:
        print(f"获取情绪趋势错误: {e}")
        return jsonify({"error": "获取情绪趋势失败"}), 500


@app.route('/api/counselor/patient/<int:patient_id>/notes', methods=['GET', 'POST'])
@login_required
def counselor_notes_api(patient_id):
    """咨询师建议API"""
    if not current_user.is_counselor():
        return jsonify({"error": "无权访问"}), 403

    # 验证患者存在
    patient = User.query.filter_by(id=patient_id, role='patient').first()
    if not patient:
        return jsonify({"error": "患者不存在"}), 404

    if request.method == 'GET':
        """获取患者的所有建议"""
        try:
            notes = CounselorNote.query.filter_by(user_id=patient_id)\
                .order_by(CounselorNote.created_at.desc())\
                .all()

            return jsonify({
                'success': True,
                'notes': [note.to_dict() for note in notes]
            })

        except Exception as e:
            print(f"获取建议错误: {e}")
            return jsonify({"error": "获取建议失败"}), 500

    elif request.method == 'POST':
        """添加新建议"""
        try:
            data = request.json
            note_type = data.get('note_type', 'suggestion')
            note_content = data.get('note', '').strip()

            if not note_content:
                return jsonify({"error": "建议内容不能为空"}), 400

            valid_types = ['suggestion', 'observation', 'warning', 'encouragement']
            if note_type not in valid_types:
                return jsonify({"error": "无效的建议类型"}), 400

            new_note = CounselorNote(
                user_id=patient_id,
                counselor_id=current_user.id,
                note_type=note_type,
                note=note_content
            )

            db.session.add(new_note)
            db.session.commit()

            print(f"[NOTE] 咨询师 {current_user.username} 给患者 {patient.username} 添加建议: {note_type}")

            return jsonify({
                'success': True,
                'note': new_note.to_dict()
            })

        except Exception as e:
            print(f"添加建议错误: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "添加建议失败"}), 500


@app.route('/api/counselor/patient/<int:patient_id>/recent-chats')
@login_required
def get_patient_recent_chats(patient_id):
    """获取患者最近的对话记录"""
    if not current_user.is_counselor():
        return jsonify({"error": "无权访问"}), 403

    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)

        chats = ChatMessage.query.filter_by(user_id=patient_id)\
            .order_by(ChatMessage.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()

        return jsonify({
            'success': True,
            'chats': [chat.to_dict() for chat in chats],
            'total': ChatMessage.query.filter_by(user_id=patient_id).count()
        })

    except Exception as e:
        print(f"获取对话记录错误: {e}")
        return jsonify({"error": "获取对话记录失败"}), 500


@app.route('/api/counselor/patient/<int:patient_id>/export-report')
@login_required
def export_patient_report(patient_id):
    """导出用户报告（仅咨询师）"""
    if not current_user.is_counselor():
        return jsonify({"error": "无权访问"}), 403

    try:
        from counselor_report_generator import CounselorReportGenerator
        from flask import Response

        # 验证患者存在
        patient = User.query.filter_by(id=patient_id, role='patient').first()
        if not patient:
            return jsonify({"error": "患者不存在"}), 404

        # 生成报告
        generator = CounselorReportGenerator(patient_id)
        html_content = generator.export_to_html()

        # 记录导出操作
        view_record = CounselorViewRecord(
            counselor_id=current_user.id,
            user_id=patient_id
        )
        db.session.add(view_record)
        db.session.commit()

        # 返回HTML文件
        filename = f"陪伴状态报告_{patient.username}_{datetime.now().strftime('%Y%m%d')}.html"
        return Response(
            html_content,
            mimetype='text/html',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        print(f"导出报告错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "导出报告失败"}), 500


@app.route('/api/counselor/patient/<int:patient_id>/report-preview')
@login_required
def preview_patient_report(patient_id):
    """预览用户报告（JSON格式）"""
    if not current_user.is_counselor():
        return jsonify({"error": "无权访问"}), 403

    try:
        from counselor_report_generator import CounselorReportGenerator

        # 验证患者存在
        patient = User.query.filter_by(id=patient_id, role='patient').first()
        if not patient:
            return jsonify({"error": "患者不存在"}), 404

        # 生成报告
        generator = CounselorReportGenerator(patient_id)
        report_data = generator.generate_report()

        return jsonify({
            'success': True,
            'report': report_data
        })

    except Exception as e:
        print(f"预览报告错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "预览报告失败"}), 500


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
    print("\n[OK] 启动服务器: http://127.0.0.1:5000")
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )
