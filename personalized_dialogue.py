"""
个性化对话策略模块 - 基于用户反馈的轻量级RLHF实现

功能:
1. 分析用户反馈历史
2. 生成个性化对话提示词
3. 动态调整对话风格
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from models import db, ConversationFeedback
import json


class PersonalizedDialogueStrategy:
    """个性化对话策略系统"""

    def __init__(self):
        self.feedback_cache = {}
        self.cache_duration = timedelta(minutes=5)

    def get_user_feedback_stats(self, user_id: int) -> Dict:
        """
        获取用户反馈统计

        Args:
            user_id: 用户ID

        Returns:
            统计数据字典
        """
        # 检查缓存
        if user_id in self.feedback_cache:
            cached_data, cache_time = self.feedback_cache[user_id]
            if datetime.now() - cache_time < self.cache_duration:
                return cached_data

        # 查询最近的反馈（最近30天）
        since_date = datetime.now() - timedelta(days=30)
        feedbacks = ConversationFeedback.query.filter(
            ConversationFeedback.user_id == user_id,
            ConversationFeedback.created_at >= since_date
        ).all()

        if not feedbacks:
            return {
                'total_count': 0,
                'positive_rate': 0.0,
                'negative_count': 0,
                'common_issues': [],
                'suggestion': None
            }

        # 统计数据
        total_count = len(feedbacks)
        positive_count = sum(1 for f in feedbacks if f.feedback_type == 'positive')
        negative_count = total_count - positive_count
        positive_rate = positive_count / total_count if total_count > 0 else 0.0

        # 分析常见问题
        negative_feedbacks = [f for f in feedbacks if f.feedback_type == 'negative']
        issue_counts = {}
        for f in negative_feedbacks:
            if f.feedback_reason:
                issue_counts[f.feedback_reason] = issue_counts.get(f.feedback_reason, 0) + 1

        # 找出最常见的问题
        common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:2]
        common_issues = [{'reason': reason, 'count': count} for reason, count in common_issues]

        # 生成建议
        suggestion = self._generate_suggestion(positive_rate, common_issues)

        stats = {
            'total_count': total_count,
            'positive_rate': round(positive_rate, 2),
            'negative_count': negative_count,
            'common_issues': common_issues,
            'suggestion': suggestion
        }

        # 缓存结果
        self.feedback_cache[user_id] = (stats, datetime.now())

        return stats

    def _generate_suggestion(self, positive_rate: float, common_issues: List[Dict]) -> Optional[str]:
        """
        根据反馈数据生成建议

        Args:
            positive_rate: 正面反馈率
            common_issues: 常见问题列表

        Returns:
            建议字符串
        """
        if positive_rate >= 0.8:
            return None  # 用户满意度高，无需调整

        suggestions = []

        # 基于常见问题的建议
        issue_mapping = {
            'inaccurate': '用户反映理解存在问题，需要更仔细地分析用户输入',
            'unclear': '用户认为回复不够清晰，需要使用更简洁明确的语言',
            'inappropriate': '用户认为内容不当，需要注意语气和专业性',
            'other': '用户有其他顾虑，需要更多同理心和关怀'
        }

        for issue in common_issues:
            reason = issue.get('reason')
            if reason in issue_mapping:
                suggestions.append(issue_mapping[reason])

        # 基于正面反馈率的建议
        if positive_rate < 0.5:
            suggestions.append('整体满意度较低，需要更谨慎和专业的回应')

        return '; '.join(suggestions) if suggestions else None

    def get_personalized_prompt(self, user_id: int, base_prompt: str = "") -> str:
        """
        获取个性化对话提示词

        Args:
            user_id: 用户ID
            base_prompt: 基础提示词

        Returns:
            个性化提示词
        """
        stats = self.get_user_feedback_stats(user_id)

        if stats['total_count'] < 3:
            # 反馈数据不足，使用基础提示词
            return base_prompt

        # 构建个性化提示词
        personalized_instructions = []

        if stats['positive_rate'] >= 0.8:
            personalized_instructions.append("用户对你的回复很满意，继续保持当前风格。")
        elif stats['positive_rate'] < 0.5:
            personalized_instructions.append("用户最近满意度较低，请更加谨慎和专业。")

        # 根据常见问题调整
        for issue in stats['common_issues']:
            reason = issue['reason']
            if reason == 'unclear':
                personalized_instructions.append("请使用简洁明了的语言，避免过于复杂的表达。")
            elif reason == 'inaccurate':
                personalized_instructions.append("请仔细分析用户的真实需求，确保理解准确。")
            elif reason == 'inappropriate':
                personalized_instructions.append("请注意专业性和语气，避免可能引起误解的表达。")

        if not personalized_instructions:
            return base_prompt

        # 组合提示词
        if base_prompt:
            return f"{base_prompt}\n\n[个性化指导]\n" + "\n".join(personalized_instructions)
        else:
            return "\n".join(personalized_instructions)

    def adjust_response_style(self, user_id: int, response: str) -> str:
        """
        根据用户反馈调整回复风格（后处理）

        Args:
            user_id: 用户ID
            response: 原始回复

        Returns:
            调整后的回复
        """
        stats = self.get_user_feedback_stats(user_id)

        if stats['total_count'] < 5:
            return response  # 数据不足，不调整

        # 如果用户经常反馈"不够清晰"，缩短回复
        unclear_count = sum(1 for issue in stats['common_issues'] if issue['reason'] == 'unclear')
        if unclear_count >= 2 and len(response) > 80:
            # 尝试在第一个句号处截断
            for punct in ['。', '！', '？']:
                if punct in response[:80]:
                    idx = response.index(punct) + 1
                    response = response[:idx].strip()
                    break

        return response

    def clear_cache(self, user_id: Optional[int] = None):
        """
        清除缓存

        Args:
            user_id: 用户ID，如果为None则清除所有缓存
        """
        if user_id is None:
            self.feedback_cache.clear()
        elif user_id in self.feedback_cache:
            del self.feedback_cache[user_id]


# 全局实例
personalized_strategy = PersonalizedDialogueStrategy()


def get_user_personalization(user_id: int) -> Dict:
    """
    获取用户个性化信息（便捷函数）

    Args:
        user_id: 用户ID

    Returns:
        个性化信息字典
    """
    return personalized_strategy.get_user_feedback_stats(user_id)


def get_personalized_prompt(user_id: int, base_prompt: str = "") -> str:
    """
    获取个性化提示词（便捷函数）

    Args:
        user_id: 用户ID
        base_prompt: 基础提示词

    Returns:
        个性化提示词
    """
    return personalized_strategy.get_personalized_prompt(user_id, base_prompt)


if __name__ == "__main__":
    """测试代码"""
    import sys
    sys.path.insert(0, '..')
    from app import app

    with app.app_context():
        # 测试：获取用户反馈统计
        print("测试个性化对话策略系统")
        print("=" * 60)

        # 假设用户ID为1
        user_id = 1
        stats = personalized_strategy.get_user_feedback_stats(user_id)

        print(f"\n用户 {user_id} 的反馈统计:")
        print(f"  总反馈数: {stats['total_count']}")
        print(f"  正面反馈率: {stats['positive_rate']}")
        print(f"  负面反馈数: {stats['negative_count']}")
        print(f"  常见问题: {stats['common_issues']}")
        print(f"  建议: {stats['suggestion']}")

        # 获取个性化提示词
        prompt = personalized_strategy.get_personalized_prompt(
            user_id,
            "你是一个专业的心理咨询助手。"
        )
        print(f"\n个性化提示词:\n{prompt}")
