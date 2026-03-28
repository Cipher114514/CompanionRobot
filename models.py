# -*- coding: utf-8 -*-
"""
数据库模型
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # 关联的评估结果
    assessment_results = db.relationship('AssessmentResult', backref='user', lazy='dynamic',
                                        cascade='all, delete-orphan')

    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class AssessmentResult(db.Model):
    """评估结果模型"""
    __tablename__ = 'assessment_results'

    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.String(100), unique=True, nullable=False, index=True)

    # 用户关联
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # 评估类型
    assessment_type = db.Column(db.String(20), nullable=False)  # 'single' 或 'comprehensive'

    # 评估结果数据（JSON格式存储）
    results_data = db.Column(db.Text, nullable=False)  # JSON字符串

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<AssessmentResult {self.result_id}>'

    def get_results(self):
        """获取解析后的结果数据"""
        import json
        return json.loads(self.results_data)

    def set_results(self, data):
        """设置结果数据（转换为JSON）"""
        import json
        self.results_data = json.dumps(data, ensure_ascii=False)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'result_id': self.result_id,
            'user_id': self.user_id,
            'assessment_type': self.assessment_type,
            'results': self.get_results(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserSession(db.Model):
    """用户会话模型"""
    __tablename__ = 'user_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    session_token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    user = db.relationship('User', backref=db.backref('sessions', lazy='dynamic'))

    def __repr__(self):
        return f'<UserSession {self.session_token}>'

    def is_valid(self):
        """检查会话是否有效"""
        return self.is_active and (self.expires_at is None or self.expires_at > datetime.utcnow())


class ChatMessage(db.Model):
    """聊天消息模型"""
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # 消息内容
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)

    # 情绪分析结果
    emotion = db.Column(db.String(20), nullable=False)  # positive, negative, neutral
    confidence = db.Column(db.Float, default=0.0)

    # 危机干预标记
    is_crisis_response = db.Column(db.Boolean, default=False, nullable=False)  # 是否为危机干预回复

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref=db.backref('chat_messages', lazy='dynamic',
                                                      cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<ChatMessage {self.id}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_message': self.user_message,
            'bot_response': self.bot_response,
            'emotion': self.emotion,
            'confidence': self.confidence,
            'is_crisis_response': self.is_crisis_response,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SentimentAnalysis(db.Model):
    """情绪分析记录表"""
    __tablename__ = 'sentiment_analyses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    chat_message_id = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=True)

    # 文本情绪分析
    text_sentiment = db.Column(db.String(20))  # positive, negative, neutral
    text_confidence = db.Column(db.Float)

    # 语音情绪分析（如果有）
    voice_sentiment = db.Column(db.String(20))
    voice_confidence = db.Column(db.Float)

    # 融合情绪分析
    overall_sentiment = db.Column(db.String(20))
    overall_confidence = db.Column(db.Float)

    # 风险指标
    risk_indicators = db.Column(db.Text)  # JSON格式存储风险特征

    # 语音特征（原始数据）
    audio_features = db.Column(db.Text)  # JSON格式存储语音特征

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关联
    user = db.relationship('User', backref=db.backref('sentiment_analyses', lazy='dynamic'))
    chat_message = db.relationship('ChatMessage', backref=db.backref('sentiment_analysis', uselist=False))

    def to_dict(self):
        """转换为字典"""
        import json
        return {
            'id': self.id,
            'text_sentiment': self.text_sentiment,
            'voice_sentiment': self.voice_sentiment,
            'overall_sentiment': self.overall_sentiment,
            'risk_indicators': json.loads(self.risk_indicators) if self.risk_indicators else {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<SentimentAnalysis {self.id}>'


class ConversationFeedback(db.Model):
    """对话反馈表 - 用于RLHF轻量级实现"""
    __tablename__ = 'conversation_feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    chat_message_id = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=False, index=True)

    # 反馈类型
    feedback_type = db.Column(db.String(10), nullable=False)  # 'positive' 或 'negative'

    # 反馈原因（可选）
    feedback_reason = db.Column(db.String(50))  # 'helpful', 'inappropriate', 'inaccurate', 'unclear', 'other'

    # 详细反馈（可选）
    feedback_text = db.Column(db.Text)

    # 用户当时的情绪状态（用于上下文分析）
    user_emotion = db.Column(db.String(20))  # positive, negative, neutral

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关联
    user = db.relationship('User', backref=db.backref('feedbacks', lazy='dynamic',
                                                       cascade='all, delete-orphan'))
    chat_message = db.relationship('ChatMessage', backref=db.backref('feedback', uselist=False))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'chat_message_id': self.chat_message_id,
            'feedback_type': self.feedback_type,
            'feedback_reason': self.feedback_reason,
            'feedback_text': self.feedback_text,
            'user_emotion': self.user_emotion,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<ConversationFeedback {self.id} - {self.feedback_type}>'


class UserStrategyProfile(db.Model):
    """用户策略画像表 - 存储个性化疗愈策略"""
    __tablename__ = 'user_strategy_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)

    # 用户画像数据（JSON格式）
    depression_level = db.Column(db.String(50))  # 抑郁程度
    trend_status = db.Column(db.String(50))  # 趋势状态
    preferred_style = db.Column(db.String(50))  # 首选对话风格

    # 画像完整数据
    profile_data = db.Column(db.Text)  # 完整画像JSON

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    user = db.relationship('User', backref=db.backref('strategy_profile', uselist=False,
                                                       cascade='all, delete-orphan'))

    def get_profile(self):
        """获取解析后的画像数据"""
        import json
        return json.loads(self.profile_data) if self.profile_data else {}

    def set_profile(self, data):
        """设置画像数据（转换为JSON）"""
        import json
        self.profile_data = json.dumps(data, ensure_ascii=False)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'depression_level': self.depression_level,
            'trend_status': self.trend_status,
            'preferred_style': self.preferred_style,
            'profile': self.get_profile(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<UserStrategyProfile {self.user_id} - {self.preferred_style}>'


class StrategyUsageLog(db.Model):
    """策略使用日志表 - 记录每次对话使用的策略"""
    __tablename__ = 'strategy_usage_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    chat_message_id = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=False, index=True)

    # 使用的策略
    strategy_type = db.Column(db.String(50), nullable=False)  # 'empathetic', 'guidance', 'solution_focused'
    strategy_name = db.Column(db.String(50), nullable=False)  # '共情型', '指导型', '解决型'

    # 策略上下文
    user_emotion = db.Column(db.String(20))  # 当时用户情绪
    depression_level = db.Column(db.String(50))  # 当时抑郁程度

    # 效果追踪（如果有反馈）
    feedback_received = db.Column(db.Boolean, default=False)
    feedback_type = db.Column(db.String(10))  # 'positive', 'negative'

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关联
    user = db.relationship('User', backref=db.backref('strategy_logs', lazy='dynamic',
                                                       cascade='all, delete-orphan'))
    chat_message = db.relationship('ChatMessage', backref=db.backref('strategy_log', uselist=False))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'chat_message_id': self.chat_message_id,
            'strategy_type': self.strategy_type,
            'strategy_name': self.strategy_name,
            'user_emotion': self.user_emotion,
            'depression_level': self.depression_level,
            'feedback_received': self.feedback_received,
            'feedback_type': self.feedback_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<StrategyUsageLog {self.id} - {self.strategy_name}>'


def init_db(app):
    """初始化数据库"""
    db.init_app(app)

    with app.app_context():
        # 创建所有表
        db.create_all()
        print("Database initialized successfully!")
