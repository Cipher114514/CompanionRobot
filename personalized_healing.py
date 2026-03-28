"""
个性化疗愈策略系统 - 渐进式实现
版本：v1.0 基础版（规则引擎 + 数据统计）
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func
from models import db, User, AssessmentResult, ChatMessage, ConversationFeedback
import json


class UserProfile:
    """用户画像标签"""

    # 抑郁程度标签
    DEPRESSION_LEVELS = {
        "minimal": "无抑郁",
        "mild": "轻度抑郁",
        "moderate": "中度抑郁",
        "moderately_severe": "中重度抑郁",
        "severe": "重度抑郁"
    }

    # 用户状态类型
    STATUS_TYPES = {
        "new_user": "新用户",
        "stable": "状态稳定",
        "improving": "正在改善",
        "fluctuating": "波动状态",
        "deteriorating": "状态恶化"
    }

    # 对话风格类型
    CONVERSATION_STYLES = {
        "empathetic": {
            "name": "共情型",
            "description": "注重倾听和理解，给予情感支持",
            "system_prompt": """你是一位温暖、共情的心理咨询师。
你的特点是：
- 多用"我能理解你的感受"、"这确实很难"等共情语言
- 倾听为主，不给太多建议
- 关注用户的情绪状态
- 语言温柔、舒缓
""",
            "suitable_for": ["moderate", "moderately_severe", "severe"]  # 适合中重度抑郁
        },
        "guidance": {
            "name": "指导型",
            "description": "提供专业建议和指导，帮助用户建立认知",
            "system_prompt": """你是一位专业、耐心的心理导师。
你的特点是：
- 提供实用的心理调节技巧
- 解释情绪背后的原因
- 给出具体的行动建议
- 语言清晰、有条理
""",
            "suitable_for": ["mild", "moderate"]  # 适合轻中度抑郁
        },
        "solution_focused": {
            "name": "解决型",
            "description": "聚焦问题解决，帮助用户制定行动计划",
            "system_prompt": """你是一位务实的心理教练。
你的特点是：
- 帮助用户识别具体问题
- 引导用户思考解决方案
- 制定可执行的小目标
- 语言积极、鼓励行动
""",
            "suitable_for": ["minimal", "mild", "improving"]  # 适合轻度抑郁或正在改善的用户
        }
    }

    # 疗愈因子类型
    HEALING_FACTORS = {
        "music": "音乐疗愈",
        "conversation": "倾诉疗愈",
        "exercise": "运动建议",
        "meditation": "冥想引导",
        "social": "社交支持"
    }


class UserProfiler:
    """用户画像分析器 - 基于历史数据生成用户标签"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user = User.query.get(user_id)

    def analyze_depression_level(self) -> Dict:
        """
        分析用户抑郁程度（基于最新的PHQ-9评估）

        Returns:
            {
                "level": "mild",
                "level_name": "轻度抑郁",
                "score": 8,
                "assessment_date": "2024-01-15"
            }
        """
        latest_phq9 = AssessmentResult.query.filter(
            AssessmentResult.user_id == self.user_id,
            AssessmentResult.assessment_type == "single"
        ).order_by(AssessmentResult.created_at.desc()).first()

        if not latest_phq9:
            return {
                "level": "unknown",
                "level_name": "未评估",
                "score": None,
                "assessment_date": None
            }

        results = latest_phq9.get_results()
        # 从综合结果中提取PHQ-9数据
        phq9_result = results.get("phq9", {})
        level = phq9_result.get("level", "unknown")

        return {
            "level": level,
            "level_name": UserProfile.DEPRESSION_LEVELS.get(level, "未知"),
            "score": phq9_result.get("total_score"),
            "assessment_date": latest_phq9.created_at.strftime("%Y-%m-%d")
        }

    def analyze_trend(self) -> Dict:
        """
        分析用户状态趋势（基于历史评估）

        Returns:
            {
                "status": "improving",
                "status_name": "正在改善",
                "trend": "score_decreased",
                "change_rate": -0.25  # 分数降低了25%
            }
        """
        # 获取最近3次PHQ-9评估
        assessments = AssessmentResult.query.filter(
            AssessmentResult.user_id == self.user_id,
            AssessmentResult.assessment_type == "single"
        ).order_by(AssessmentResult.created_at.desc()).limit(3).all()

        if len(assessments) < 2:
            return {
                "status": "new_user",
                "status_name": UserProfile.STATUS_TYPES["new_user"],
                "trend": "insufficient_data",
                "change_rate": 0
            }

        # 提取PHQ-9分数
        scores = []
        for assessment in assessments:
            results = assessment.get_results()
            phq9 = results.get("phq9", {})
            score = phq9.get("total_score", 0)
            scores.append(score)

        if len(scores) < 2:
            return {
                "status": "new_user",
                "status_name": UserProfile.STATUS_TYPES["new_user"],
                "trend": "insufficient_data",
                "change_rate": 0
            }

        # 计算趋势
        latest_score = scores[0]
        previous_avg_score = sum(scores[1:]) / len(scores[1:])
        change_rate = (latest_score - previous_avg_score) / (previous_avg_score + 0.01)  # 避免除零

        # 判断状态
        if change_rate < -0.15:  # 分数降低超过15%
            status = "improving"
            trend = "score_decreased"
        elif change_rate > 0.15:  # 分数上升超过15%
            status = "deteriorating"
            trend = "score_increased"
        elif abs(change_rate) <= 0.15:  # 分数波动小于15%
            # 检查是否持续波动
            variance = sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)
            if variance > 4:  # 方差较大
                status = "fluctuating"
                trend = "fluctuating"
            else:
                status = "stable"
                trend = "stable"
        else:
            status = "stable"
            trend = "stable"

        return {
            "status": status,
            "status_name": UserProfile.STATUS_TYPES.get(status, "未知"),
            "trend": trend,
            "change_rate": round(change_rate * 100, 1)  # 转换为百分比
        }

    def analyze_conversation_preference(self) -> Dict:
        """
        分析用户对话偏好（基于反馈数据）

        Returns:
            {
                "preferred_style": "empathetic",
                "effectiveness": {
                    "empathetic": 0.75,  # 共情型75%正面反馈
                    "guidance": 0.60,
                    "solution_focused": 0.45
                }
            }
        """
        # 获取该用户的所有反馈记录
        feedbacks = ConversationFeedback.query.filter(
            ConversationFeedback.user_id == self.user_id
        ).all()

        if len(feedbacks) < 5:  # 反馈样本太少
            return {
                "preferred_style": None,
                "effectiveness": {},
                "note": "反馈样本不足，需要更多对话数据"
            }

        # TODO: 这里需要关联对话时使用的策略
        # 目前先返回空字典，等策略系统建立后再完善
        return {
            "preferred_style": None,
            "effectiveness": {},
            "total_feedbacks": len(feedbacks),
            "note": "策略追踪功能将在下一版本实现"
        }

    def generate_profile(self) -> Dict:
        """
        生成完整的用户画像

        Returns:
            {
                "user_id": 1,
                "depression_level": {...},
                "trend": {...},
                "conversation_preference": {...},
                "recommended_style": "empathetic",
                "generated_at": "2024-01-15 10:30:00"
            }
        """
        depression_level = self.analyze_depression_level()
        trend = self.analyze_trend()
        preference = self.analyze_conversation_preference()

        # 推荐对话风格（基于抑郁程度）
        level = depression_level.get("level", "unknown")
        status = trend.get("status", "new_user")

        # 推荐逻辑
        recommended_style = None

        # 优先级1：重度抑郁 → 共情型
        if level in ["moderately_severe", "severe"]:
            recommended_style = "empathetic"
        # 优先级2：正在改善 → 解决型
        elif status == "improving":
            recommended_style = "solution_focused"
        # 优先级3：轻度/中度 → 指导型
        elif level in ["minimal", "mild", "moderate"]:
            recommended_style = "guidance"
        # 优先级4：状态恶化 → 共情型
        elif status == "deteriorating":
            recommended_style = "empathetic"
        # 默认：指导型
        else:
            recommended_style = "guidance"

        return {
            "user_id": self.user_id,
            "depression_level": depression_level,
            "trend": trend,
            "conversation_preference": preference,
            "recommended_style": recommended_style,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


class StrategyRecommender:
    """疗愈策略推荐引擎"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.profiler = UserProfiler(user_id)

    def get_conversation_style(self) -> Dict:
        """
        获取推荐的对话风格

        Returns:
            {
                "style_id": "empathetic",
                "style_name": "共情型",
                "system_prompt": "...",
                "reason": "用户为中重度抑郁，需要更多情感支持"
            }
        """
        profile = self.profiler.generate_profile()
        style_id = profile.get("recommended_style", "guidance")

        style_info = UserProfile.CONVERSATION_STYLES[style_id]

        # 生成推荐理由
        reason = self._generate_reason(profile, style_id)

        return {
            "style_id": style_id,
            "style_name": style_info["name"],
            "description": style_info["description"],
            "system_prompt": style_info["system_prompt"],
            "reason": reason
        }

    def _generate_reason(self, profile: Dict, style_id: str) -> str:
        """生成推荐理由"""
        level_info = profile["depression_level"]
        trend_info = profile["trend"]

        level_name = level_info.get("level_name", "")
        status_name = trend_info.get("status_name", "")

        if style_id == "empathetic":
            return f"用户当前状态：{level_name}，{status_name}。需要更多情感支持和倾听。"
        elif style_id == "guidance":
            return f"用户当前状态：{level_name}，{status_name}。适合提供专业建议和指导。"
        elif style_id == "solution_focused":
            return f"用户当前状态：{status_name}。适合聚焦问题解决和行动计划。"
        else:
            return "根据用户画像推荐"

    def get_healing_factors(self) -> List[Dict]:
        """
        获取推荐的疗愈因子

        Returns:
            [
                {
                    "factor_id": "music",
                    "factor_name": "音乐疗愈",
                    "priority": 1,
                    "reason": "..."
                },
                ...
            ]
        """
        profile = self.profiler.generate_profile()
        level = profile["depression_level"].get("level")
        status = profile["trend"].get("status")

        factors = []

        # 基础推荐：所有用户都适合音乐疗愈
        factors.append({
            "factor_id": "music",
            "factor_name": UserProfile.HEALING_FACTORS["music"],
            "priority": 1,
            "reason": "音乐能有效缓解焦虑和低落情绪"
        })

        # 根据抑郁程度推荐
        if level in ["moderate", "moderately_severe", "severe"]:
            factors.append({
                "factor_id": "conversation",
                "factor_name": UserProfile.HEALING_FACTORS["conversation"],
                "priority": 2,
                "reason": "建议多与信任的人倾诉，释放情绪压力"
            })
            factors.append({
                "factor_id": "meditation",
                "factor_name": UserProfile.HEALING_FACTORS["meditation"],
                "priority": 3,
                "reason": "冥想有助于平复情绪，减少负面思维"
            })

        # 根据状态推荐
        if status == "improving":
            factors.append({
                "factor_id": "exercise",
                "factor_name": UserProfile.HEALING_FACTORS["exercise"],
                "priority": 2,
                "reason": "你正在改善！适量运动能帮助巩固疗愈效果"
            })
        elif status == "stable":
            factors.append({
                "factor_id": "social",
                "factor_name": UserProfile.HEALING_FACTORS["social"],
                "priority": 2,
                "reason": "你的状态稳定，可以尝试更多社交活动"
            })

        # 按优先级排序
        factors.sort(key=lambda x: x["priority"])

        return factors

    def generate_strategy_report(self) -> Dict:
        """
        生成完整的疗愈策略报告

        Returns:
            {
                "user_profile": {...},
                "conversation_strategy": {...},
                "healing_factors": [...],
                "next_review_date": "2024-02-15"
            }
        """
        profile = self.profiler.generate_profile()
        conversation_style = self.get_conversation_style()
        healing_factors = self.get_healing_factors()

        # 下次评估时间：30天后
        next_review = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        return {
            "user_profile": profile,
            "conversation_strategy": conversation_style,
            "healing_factors": healing_factors,
            "next_review_date": next_review,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# ==================== 辅助函数 ====================

def get_user_strategy(user_id: int) -> Dict:
    """
    获取用户的疗愈策略（快捷接口）

    Args:
        user_id: 用户ID

    Returns:
        策略报告字典
    """
    recommender = StrategyRecommender(user_id)
    return recommender.generate_strategy_report()


def update_user_profile(user_id: int) -> Dict:
    """
    更新用户画像（快捷接口）

    Args:
        user_id: 用户ID

    Returns:
        用户画像字典
    """
    profiler = UserProfiler(user_id)
    return profiler.generate_profile()


if __name__ == "__main__":
    # 测试代码
    print("个性化疗愈策略系统 - 测试\n")

    # 创建测试用户画像
    test_user_id = 1
    profiler = UserProfiler(test_user_id)
    profile = profiler.generate_profile()

    print("=" * 50)
    print("用户画像分析结果")
    print("=" * 50)
    print(json.dumps(profile, ensure_ascii=False, indent=2))

    # 获取疗愈策略
    recommender = StrategyRecommender(test_user_id)
    strategy = recommender.generate_strategy_report()

    print("\n" + "=" * 50)
    print("疗愈策略报告")
    print("=" * 50)
    print(json.dumps(strategy, ensure_ascii=False, indent=2))
