"""
咨询师报告生成器
专业陪伴视角，非医疗治疗视角
"""

from datetime import datetime, timedelta, date
from typing import Dict, List
import json
from models import User, ChatMessage, CounselorNote
from sqlalchemy import func


class CounselorReportGenerator:
    """咨询师报告生成器"""

    def __init__(self, patient_id: int):
        self.patient_id = patient_id
        self.patient = User.query.filter_by(id=patient_id, role='patient').first()

    def generate_report(self) -> Dict:
        """生成完整报告"""
        if not self.patient:
            return {'error': '用户不存在'}

        return {
            'report_info': self._get_report_info(),
            'user_profile': self._get_user_profile(),
            'activity_overview': self._get_activity_overview(),
            'emotion_trend': self._get_emotion_trend(),
            'conversation_summary': self._get_conversation_summary(),
            'key_events': self._get_key_events(),
            'counselor_notes': self._get_counselor_notes(),
            '陪伴建议': self._generate_companionship_suggestions(),
            'attention_points': self._get_attention_points()
        }

    def _get_report_info(self) -> Dict:
        """报告基本信息"""
        return {
            'report_title': f'陪伴状态报告 - {self.patient.username}',
            'generated_at': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
            'report_type': '咨询师专业视角',
            'perspective': '日常陪伴与情感支持'
        }

    def _get_user_profile(self) -> Dict:
        """用户基本信息"""
        age = None
        if self.patient.birth_date:
            today = date.today()
            age = today.year - self.patient.birth_date.year - (
                (today.month, today.day) < (self.patient.birth_date.month, self.patient.birth_date.day)
            )

        # 计算注册天数
        days_since_register = (datetime.now() - self.patient.created_at).days

        return {
            'username': self.patient.username,
            'age': age,
            'registration_date': self.patient.created_at.strftime('%Y年%m月%d日'),
            'days_since_register': days_since_register,
            'last_active': self._get_last_active()
        }

    def _get_last_active(self) -> str:
        """最后活跃时间"""
        latest_chat = ChatMessage.query.filter_by(user_id=self.patient_id)\
            .order_by(ChatMessage.created_at.desc()).first()

        if not latest_chat:
            return '暂无对话记录'

        days = (datetime.now() - latest_chat.created_at).days
        if days == 0:
            return '今天活跃'
        elif days == 1:
            return '昨天活跃'
        elif days <= 7:
            return f'{days}天前活跃'
        else:
            return f'{days}天前活跃（需关注）'

    def _get_activity_overview(self) -> Dict:
        """活跃度概览"""
        total_chats = ChatMessage.query.filter_by(user_id=self.patient_id).count()

        # 最近7天对话数
        week_ago = datetime.now() - timedelta(days=7)
        week_chats = ChatMessage.query.filter(
            ChatMessage.user_id == self.patient_id,
            ChatMessage.created_at >= week_ago
        ).count()

        # 最近30天对话数
        month_ago = datetime.now() - timedelta(days=30)
        month_chats = ChatMessage.query.filter(
            ChatMessage.user_id == self.patient_id,
            ChatMessage.created_at >= month_ago
        ).count()

        # 平均每天对话数
        avg_daily = round(month_chats / 30, 1) if month_chats > 0 else 0

        return {
            'total_conversations': total_chats,
            'week_conversations': week_chats,
            'month_conversations': month_chats,
            'avg_daily_conversations': avg_daily,
            'activity_level': self._assess_activity_level(week_chats)
        }

    def _assess_activity_level(self, week_chats: int) -> str:
        """评估活跃度"""
        if week_chats == 0:
            return '未活跃'
        elif week_chats <= 3:
            return '低活跃'
        elif week_chats <= 10:
            return '中等活跃'
        else:
            return '高活跃'

    def _get_emotion_trend(self) -> Dict:
        """情绪趋势分析（非症状分析）"""
        # 最近30天的情绪分布
        month_ago = datetime.now() - timedelta(days=30)
        emotions = ChatMessage.query.filter(
            ChatMessage.user_id == self.patient_id,
            ChatMessage.created_at >= month_ago
        ).all()

        if not emotions:
            return {'note': '暂无情绪记录'}

        emotion_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for e in emotions:
            emotion_counts[e.emotion] = emotion_counts.get(e.emotion, 0) + 1

        total = len(emotions)
        emotion_percentages = {
            k: round(v / total * 100, 1) if total > 0 else 0
            for k, v in emotion_counts.items()
        }

        # 情绪状态评估（非诊断）
        dominant = max(emotion_counts.items(), key=lambda x: x[1])[0]
        emotion_state_map = {
            'positive': '整体状态积极',
            'negative': '需要关注和支持',
            'neutral': '情绪平稳'
        }

        return {
            'emotion_distribution': emotion_percentages,
            'dominant_emotion': dominant,
            'overall_state': emotion_state_map.get(dominant, '状态平稳'),
            'positive_ratio': emotion_percentages['positive']
        }

    def _get_conversation_summary(self) -> Dict:
        """对话摘要"""
        # 获取最近10次对话
        recent_chats = ChatMessage.query.filter_by(user_id=self.patient_id)\
            .order_by(ChatMessage.created_at.desc())\
            .limit(10)\
            .all()

        if not recent_chats:
            return {'note': '暂无对话记录'}

        # 提取高频话题（简单版本：关键词）
        all_messages = [chat.user_message for chat in recent_chats]
        common_topics = self._extract_common_topics(all_messages)

        # 平均对话长度
        avg_length = sum(len(msg.user_message) for msg in recent_chats) / len(recent_chats)

        return {
            'recent_conversation_count': len(recent_chats),
            'avg_message_length': round(avg_length, 0),
            'communication_style': self._assess_communication_style(avg_length),
            'common_topics': common_topics[:5]  # 最多5个话题
        }

    def _extract_common_topics(self, messages: List[str]) -> List[str]:
        """提取常见话题（简化版）"""
        # 常见关键词
        keywords = {
            '学习': ['学习', '考试', '作业', '成绩', '学校'],
            '工作': ['工作', '加班', '同事', '老板', '公司'],
            '家庭': ['家人', '父母', '孩子', '家庭', '回家'],
            '情绪': ['开心', '难过', '焦虑', '压力', '紧张'],
            '睡眠': ['失眠', '睡眠', '做梦', '睡不着'],
            '社交': ['朋友', '社交', '聚会', '孤独', '聊天']
        }

        topic_counts = {}
        for msg in messages:
            for topic, words in keywords.items():
                if any(word in msg for word in words):
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # 按频率排序
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics]

    def _assess_communication_style(self, avg_length: float) -> str:
        """评估交流风格"""
        if avg_length < 20:
            return '简短直接'
        elif avg_length < 50:
            return '适中表达'
        else:
            return '详细倾诉'

    def _get_key_events(self) -> List[Dict]:
        """关键事件记录（非危机事件）"""
        # 获取带有危机干预标记的对话
        crisis_chats = ChatMessage.query.filter(
            ChatMessage.user_id == self.patient_id,
            ChatMessage.is_crisis_response == True
        ).order_by(ChatMessage.created_at.desc()).limit(5).all()

        events = []
        for chat in crisis_chats:
            events.append({
                'date': chat.created_at.strftime('%Y年%m月%d日'),
                'content': chat.user_message[:100] + '...' if len(chat.user_message) > 100 else chat.user_message,
                'type': '需要关注的情绪表达'
            })

        return events

    def _get_counselor_notes(self) -> List[Dict]:
        """咨询师观察记录"""
        notes = CounselorNote.query.filter_by(user_id=self.patient_id)\
            .order_by(CounselorNote.created_at.desc())\
            .limit(10)\
            .all()

        return [
            {
                'date': note.created_at.strftime('%Y年%m月%d日'),
                'type': note.note_type,
                'content': note.note,
                'counselor': note.counselor.username if note.counselor else '未知'
            }
            for note in notes
        ]

    def _generate_companionship_suggestions(self) -> List[str]:
        """生成陪伴建议（非治疗建议）"""
        suggestions = []

        # 基于活跃度的建议
        activity = self._get_activity_overview()
        if activity['week_conversations'] == 0:
            suggestions.append('建议主动关心用户的近况，了解是否遇到困难')
        elif activity['week_conversations'] >= 10:
            suggestions.append('用户活跃度较高，当前陪伴频率适当')

        # 基于情绪状态的建议
        emotion = self._get_emotion_trend()
        if 'positive_ratio' in emotion:
            if emotion['positive_ratio'] < 30:
                suggestions.append('用户近期积极情绪比例较低，建议给予更多鼓励和支持')
            elif emotion['positive_ratio'] > 70:
                suggestions.append('用户整体状态良好，可继续保持当前陪伴方式')

        # 通用建议
        if not suggestions:
            suggestions.append('继续保持定期的陪伴和关心')

        return suggestions

    def _get_attention_points(self) -> List[str]:
        """需要关注的事项"""
        points = []

        activity = self._get_activity_overview()
        if activity['week_conversations'] == 0:
            points.append('⚠️ 用户一周未活跃，建议主动联系')

        emotion = self._get_emotion_trend()
        if 'positive_ratio' in emotion and emotion['positive_ratio'] < 20:
            points.append('⚠️ 情绪状态偏低，需要更多关注和支持')

        # 危机事件检查
        crisis_count = ChatMessage.query.filter(
            ChatMessage.user_id == self.patient_id,
            ChatMessage.is_crisis_response == True
        ).count()

        if crisis_count > 0:
            points.append(f'⚠️ 历史有{crisis_count}次需要重点关注的情况')

        if not points:
            points.append('✓ 当前状态平稳，保持定期关注即可')

        return points

    def export_to_html(self) -> str:
        """导出为HTML格式"""
        report = self.generate_report()

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report['report_info']['report_title']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft YaHei", sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f7fa;
        }}
        .report-container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            font-size: 20px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .info-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }}
        .info-label {{
            font-size: 12px;
            color: #7f8c8d;
            margin-bottom: 5px;
        }}
        .info-value {{
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
        }}
        .stat-card {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            display: inline-block;
            margin: 5px;
            min-width: 120px;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: 700;
            color: #2c3e50;
        }}
        .stat-label {{
            font-size: 12px;
            color: #7f8c8d;
        }}
        .emotion-bar {{
            height: 30px;
            border-radius: 15px;
            display: inline-block;
            margin: 5px;
            line-height: 30px;
            color: white;
            font-weight: 600;
            text-align: center;
        }}
        .positive {{ background: #27ae60; }}
        .negative {{ background: #e74c3c; }}
        .neutral {{ background: #95a5a6; }}
        .suggestion-box {{
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .attention-item {{
            background: #fff3cd;
            border-left: 4px solid #f39c12;
            padding: 12px;
            margin: 8px 0;
            border-radius: 4px;
        }}
        .note-item {{
            background: #f8f9fa;
            padding: 12px;
            margin: 8px 0;
            border-radius: 4px;
            border-left: 3px solid #bdc3c7;
        }}
        .event-item {{
            background: #ffeaa7;
            padding: 12px;
            margin: 8px 0;
            border-radius: 4px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <h1>{report['report_info']['report_title']}</h1>
        <p style="color: #7f8c8d;">
            生成时间：{report['report_info']['generated_at']} |
            报告类型：{report['report_info']['report_type']}
        </p>

        <h2>📋 用户基本信息</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">用户名</div>
                <div class="info-value">{report['user_profile']['username']}</div>
            </div>
            <div class="info-item">
                <div class="info-label">年龄</div>
                <div class="info-value">{report['user_profile']['age'] or '未知'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">注册时间</div>
                <div class="info-value">{report['user_profile']['registration_date']}</div>
            </div>
            <div class="info-item">
                <div class="info-label">最后活跃</div>
                <div class="info-value">{report['user_profile']['last_active']}</div>
            </div>
        </div>

        <h2>📊 活跃度概览</h2>
        <div style="text-align: center; margin: 20px 0;">
            <div class="stat-card">
                <div class="stat-value">{report['activity_overview']['total_conversations']}</div>
                <div class="stat-label">总对话次数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report['activity_overview']['week_conversations']}</div>
                <div class="stat-label">本周对话</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report['activity_overview']['month_conversations']}</div>
                <div class="stat-label">本月对话</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report['activity_overview']['avg_daily_conversations']}</div>
                <div class="stat-label">日均对话</div>
            </div>
        </div>
        <p style="text-align: center; color: #7f8c8d;">
            活跃度评估：<strong>{report['activity_overview']['activity_level']}</strong>
        </p>

        <h2>😊 情绪状态分析</h2>
        <div style="text-align: center; margin: 20px 0;">
            <div class="emotion-bar positive" style="width: {report['emotion_trend'].get('emotion_distribution', {}).get('positive', 0)}%;">
                积极 {report['emotion_trend'].get('emotion_distribution', {}).get('positive', 0)}%
            </div>
            <div class="emotion-bar neutral" style="width: {report['emotion_trend'].get('emotion_distribution', {}).get('neutral', 0)}%;">
                平稳 {report['emotion_trend'].get('emotion_distribution', {}).get('neutral', 0)}%
            </div>
            <div class="emotion-bar negative" style="width: {report['emotion_trend'].get('emotion_distribution', {}).get('negative', 0)}%;">
                需要关注 {report['emotion_trend'].get('emotion_distribution', {}).get('negative', 0)}%
            </div>
        </div>
        <p style="text-align: center; font-size: 16px; color: #2c3e50;">
            整体状态：<strong>{report['emotion_trend'].get('overall_state', '状态平稳')}</strong>
        </p>

        <h2>📝 交流特点</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">交流风格</div>
                <div class="info-value">{report['conversation_summary'].get('communication_style', '未知')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">常见话题</div>
                <div class="info-value">{', '.join(report['conversation_summary'].get('common_topics', ['暂无']))}</div>
            </div>
        </div>

        <h2>⚠️ 需要关注的情况</h2>
        {self._render_attention_points(report['attention_points'])}

        <h2>💡 陪伴建议</h2>
        {self._render_suggestions(report['陪伴建议'])}

        <h2>📌 咨询师观察记录</h2>
        {self._render_counselor_notes(report['counselor_notes'])}

        <h2>🔔 关键事件记录</h2>
        {self._render_key_events(report['key_events'])}

        <div class="footer">
            <p>本报告基于陪伴平台数据生成，旨在为日常情感陪伴提供参考</p>
            <p>本平台不提供医学诊断或治疗，如有需要请引导用户寻求专业帮助</p>
            <p>生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
        """
        return html

    def _render_attention_points(self, points: List[str]) -> str:
        """渲染关注事项"""
        if not points:
            return '<p>暂无特别关注事项</p>'
        return '\n'.join([f'<div class="attention-item">{p}</div>' for p in points])

    def _render_suggestions(self, suggestions: List[str]) -> str:
        """渲染建议"""
        if not suggestions:
            return '<p>暂无特殊建议</p>'
        return '\n'.join([f'<div class="suggestion-box">💡 {s}</div>' for s in suggestions])

    def _render_counselor_notes(self, notes: List[Dict]) -> str:
        """渲染咨询师记录"""
        if not notes:
            return '<p>暂无观察记录</p>'
        return '\n'.join([
            f'<div class="note-item"><strong>{note["date"]} - {note["type"]}</strong><br>{note["content"]}<br><small>记录人：{note["counselor"]}</small></div>'
            for note in notes
        ])

    def _render_key_events(self, events: List[Dict]) -> str:
        """渲染关键事件"""
        if not events:
            return '<p>暂无需要特别关注的事件</p>'
        return '\n'.join([
            f'<div class="event-item"><strong>{event["date"]}</strong> - {event["type"]}<br>{event["content"]}</div>'
            for event in events
        ])
