# -*- coding: utf-8 -*-
"""
数据库模型 - 精简版（移除量表相关）
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

    # 用户角色: 'patient' (患者/普通用户) 或 'counselor' (心理咨询师)
    role = db.Column(db.String(20), nullable=False, default='patient', index=True)

    # 出生日期 (仅对患者)
    birth_date = db.Column(db.Date, nullable=True)

    # 用户画像字段 (JSON格式存储)
    profile_name = db.Column(db.String(50))  # 用户昵称/名字
    profile_age = db.Column(db.Integer)  # 用户画像中的年龄（可能与实际年龄不同）
    profile_job = db.Column(db.String(100))  # 职业
    profile_hobbies = db.Column(db.Text)  # 爱好列表（JSON格式）
    profile_concerns = db.Column(db.Text)  # 困扰/问题列表（JSON格式）
    profile_preferences = db.Column(db.Text)  # 对话偏好（JSON格式）
    profile_last_updated = db.Column(db.DateTime)  # 画像最后更新时间

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def is_patient(self):
        """是否是患者"""
        return self.role == 'patient'

    def is_counselor(self):
        """是否是心理咨询师"""
        return self.role == 'counselor'

    def get_profile_data(self):
        """获取用户画像数据（支持置信度和元数据）"""
        import json

        # 解析preferences字段（可能包含confidence和metadata）
        preferences_data = {}
        confidence_data = {
            'name': 0.0,
            'age': 0.0,
            'job': 0.0,
            'hobbies': {},
            'concerns': {}
        }
        metadata_data = {
            'total_messages_analyzed': 0,
            'extraction_sources': []
        }

        if self.profile_preferences:
            try:
                parsed = json.loads(self.profile_preferences)
                # 兼容旧格式（直接是preferences）和新格式（包含confidence和metadata）
                if isinstance(parsed, dict) and 'preferences' in parsed:
                    preferences_data = parsed['preferences']
                    confidence_data = parsed.get('confidence', confidence_data)
                    metadata_data = parsed.get('metadata', metadata_data)
                else:
                    preferences_data = parsed
            except:
                preferences_data = {}

        return {
            'name': self.profile_name,
            'age': self.profile_age,
            'job': self.profile_job,
            'hobbies': json.loads(self.profile_hobbies) if self.profile_hobbies else [],
            'concerns': json.loads(self.profile_concerns) if self.profile_concerns else [],
            'preferences': preferences_data,
            'confidence': confidence_data,
            'metadata': metadata_data,
            'last_updated': self.profile_last_updated.isoformat() if self.profile_last_updated else None
        }

    def update_profile_field(self, field, value):
        """更新单个画像字段"""
        import json
        if field in ['name', 'age', 'job']:
            setattr(self, f'profile_{field}', value)
        elif field in ['hobbies', 'concerns']:
            current = getattr(self, f'profile_{field}')
            current_list = json.loads(current) if current else []
            if value not in current_list:
                current_list.append(value)
            setattr(self, f'profile_{field}', json.dumps(current_list, ensure_ascii=False))
        elif field == 'preferences':
            current = self.profile_preferences
            current_prefs = json.loads(current) if current else {}
            current_prefs.update(value)
            self.profile_preferences = json.dumps(current_prefs, ensure_ascii=False)

        self.profile_last_updated = datetime.utcnow()

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
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
    is_crisis_response = db.Column(db.Boolean, default=False, nullable=False)

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


class CounselorNote(db.Model):
    """咨询师建议/留言表"""
    __tablename__ = 'counselor_notes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    counselor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # 建议类型
    note_type = db.Column(db.String(50), nullable=False)  # 'suggestion', 'observation', 'warning', 'encouragement'

    # 建议内容
    note = db.Column(db.Text, nullable=False)

    # 是否已读（用户端）
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    user = db.relationship('User', foreign_keys=[user_id],
                          backref=db.backref('received_notes', lazy='dynamic',
                                            cascade='all, delete-orphan'))
    counselor = db.relationship('User', foreign_keys=[counselor_id],
                               backref=db.backref('sent_notes', lazy='dynamic',
                                                 cascade='all, delete-orphan'))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'counselor_id': self.counselor_id,
            'counselor_name': self.counselor.username if self.counselor else None,
            'note_type': self.note_type,
            'note': self.note,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<CounselorNote {self.id} - {self.note_type}>'


class CounselorViewRecord(db.Model):
    """咨询师查看用户记录"""
    __tablename__ = 'counselor_view_records'

    id = db.Column(db.Integer, primary_key=True)
    counselor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # 查看详情
    view_duration = db.Column(db.Integer, default=0)  # 查看时长（秒）

    # 时间戳
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关联
    counselor = db.relationship('User', foreign_keys=[counselor_id],
                               backref=db.backref('view_records', lazy='dynamic',
                                                 cascade='all, delete-orphan'))
    user = db.relationship('User', foreign_keys=[user_id],
                          backref=db.backref('been_viewed_records', lazy='dynamic'))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'counselor_id': self.counselor_id,
            'user_id': self.user_id,
            'view_duration': self.view_duration,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None
        }

    def __repr__(self):
        return f'<CounselorViewRecord counselor:{self.counselor_id} -> user:{self.user_id}>'


def init_db(app):
    """初始化数据库"""
    db.init_app(app)

    with app.app_context():
        # 创建所有表
        db.create_all()
        print("Database initialized successfully!")
