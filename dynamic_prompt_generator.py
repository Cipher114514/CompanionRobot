"""
动态Prompt生成系统 - 阶段2优化版
功能：基于抑郁程度、时间段、情绪状态生成个性化system prompt

优化重点：
1. 病耻感友好 - 避免医学标签，关注"感受"而非"诊断"
2. 精简高效 - 控制Prompt长度，避免回答不完整
3. 清晰指令 - 避免指令冲突，提升生成质量

作者：AI助手
版本：v2.1 - 阶段2优化版（病耻感友好 + 性能优化）
"""

from datetime import datetime, time
from typing import Dict, Optional
from models import db, User, UserStrategyProfile, ChatMessage, SentimentAnalysis
from sqlalchemy import func


class DynamicPromptGenerator:
    """动态Prompt生成器 - 阶段2优化版（病耻感友好）"""

    # 病耻感友好的描述映射
    STIGMA_FRIENDLY_LEVELS = {
        "minimal": "状态不错",
        "mild": "有些起伏",
        "moderate": "比较辛苦",
        "moderately_severe": "承受压力",
        "severe": "非常辛苦",
        "unknown": "刚开始交流"
    }

    def __init__(self, user_id: int, stigma_aware: bool = True):
        """
        初始化Prompt生成器

        Args:
            user_id: 用户ID
            stigma_aware: 是否启用病耻感友好模式（默认True）
        """
        self.user_id = user_id
        self.user = User.query.get(user_id)
        self.strategy_profile = UserStrategyProfile.query.filter_by(
            user_id=user_id
        ).first()
        self.stigma_aware = stigma_aware  # 病耻感感知模式

    def generate_system_prompt(self) -> str:
        """
        生成个性化system prompt（优化版）

        优化点：
        1. 精简内容，控制长度在600-800字符
        2. 病耻感友好，避免医学标签
        3. 清晰的核心指令，避免冲突

        Returns:
            完整的system prompt字符串
        """
        # 1. 基础角色定义（精简版）
        base_role = self._get_base_role_prompt_compact()

        # 2. 情绪状态调整（精简版）
        emotion_adaptation = self._get_emotion_adaptation_compact()

        # 3. 时间段调整（精简版）
        time_adjustment = self._get_time_adjustment_compact()

        # 4. 安全约束（精简版）
        safety_constraints = self._get_safety_constraints_compact()

        # 组装完整prompt（优化格式）
        full_prompt = f"""{base_role}

{emotion_adaptation}

{time_adjustment}

{safety_constraints}"""

        return full_prompt.strip()

    def _get_base_role_prompt(self) -> str:
        """
        根据抑郁程度选择基础角色prompt

        Returns:
            角色定义字符串
        """
        # 获取抑郁程度
        if self.strategy_profile:
            depression_level = self.strategy_profile.depression_level
        else:
            # 新用户默认为轻度
            depression_level = "mild"

        # 角色prompt映射
        role_prompts = {
            "minimal": """【角色定位】你是一位友好的心理陪伴者。

【对话风格】
- 语言轻松、温暖
- 关注积极方面
- 鼓励健康习惯
- 像朋友一样聊天""",

            "mild": """【角色定位】你是一位积极、鼓励性的心理教练。

【对话风格】
- 提供实用建议
- 设定可达成的目标
- 强化积极行为
- 平衡共情与指导""",

            "moderate": """【角色定位】你是一位专业、耐心的心理咨询师。

【对话风格】
- 平衡共情与指导
- 提供专业建议
- 帮助建立认知
- 温和而坚定""",

            "moderately_severe": """【角色定位】你是一位温暖、共情的心理咨询师。

【对话风格】
- 多用"我能理解你的感受"、"这确实很难"等共情语言
- 倾听为主，不给太多建议
- 关注用户的情绪状态
- 语言温柔、舒缓
- 强调陪伴和安全感""",

            "severe": """【角色定位】你是一位极度温柔、耐心的心理咨询师。

【对话风格】
- ⚠️ 极度强调安全感和陪伴
- ⚠️ 避免任何压力或要求
- ⚠️ 多表达"我在这里"、"你不是一个人"
- ⚠️ 语言极度缓慢、温和
- ⚠️ 不尝试解决问题，只提供陪伴和情感支持"""
        }

        # 如果没有匹配的级别，使用默认（轻度）
        return role_prompts.get(
            depression_level,
            role_prompts["mild"]
        )

    def _get_base_role_prompt_compact(self) -> str:
        """
        精简版基础角色定义（病耻感友好）

        优化点：
        1. 去除医学标签（不说"抑郁症"）
        2. 精简到核心指令（约100-150字符）
        3. 关注"感受"而非"诊断"

        Returns:
            精简的角色定义字符串
        """
        # 获取抑郁程度
        if self.strategy_profile:
            depression_level = self.strategy_profile.depression_level
        else:
            depression_level = "mild"

        # 病耻感友好的精简角色定义（强调简洁输出）
        role_prompts_compact = {
            "minimal": """你是一位友好的心理陪伴者。关注用户的情绪，给予适当的倾听和支持。

回复要求：60-100字，简短共情+2个方法+鼓励，必须简洁。""",

            "mild": """你是一位温暖的心理陪伴者。善于倾听，给予情感支持，温柔地回应。

回复要求：60-100字，简短共情+2个方法+鼓励，必须简洁。""",

            "moderate": """你是一位耐心的心理陪伴者。多倾听、多共情，关注用户的感受。

回复要求：60-100字，简短共情+2个方法+鼓励，必须简洁。""",

            "moderately_severe": """你是一位温柔的心理陪伴者。给予充分的共情和陪伴，强调"我在这里陪你"。

回复要求：60-100字，简短共情+2个方法+鼓励，必须简洁。""",

            "severe": """你是一位极度温柔的心理陪伴者。提供安全感和陪伴，用温和的语言表达关心。

回复要求：60-100字，简短共情+2个方法+鼓励，必须简洁。"""
        }

        return role_prompts_compact.get(
            depression_level,
            role_prompts_compact["mild"]
        )

    def _get_emotion_adaptation(self) -> str:
        """
        根据用户最近的对话情绪生成适应策略

        阶段2新增功能：分析最近3-5次对话的情绪状态

        Returns:
            情绪适应策略字符串
        """
        # 获取最近3次对话的情绪
        recent_emotions = self._get_recent_emotions(n=3)

        if not recent_emotions:
            # 没有历史情绪数据，返回空字符串
            return ""

        # 分析情绪分布
        from collections import Counter
        emotion_counts = Counter(recent_emotions)

        # 判断主导情绪
        dominant_emotion = emotion_counts.most_common(1)[0][0]
        dominant_count = emotion_counts[dominant_emotion]
        total_count = len(recent_emotions)

        # 判断情绪一致性（是否连续3次都是同一情绪）
        is_consistent = dominant_count == total_count

        # 判断情绪趋势（最近一次情绪）
        latest_emotion = recent_emotions[-1] if recent_emotions else "neutral"

        # 生成适应策略
        if is_consistent and dominant_emotion == "negative":
            # 持续负面情绪
            return """【当前情绪状态：持续负面】⚠️

用户最近多次对话呈现负面情绪，需要额外关注和共情。

对话策略调整：
✅ 增加共情表达
- 多使用"我能理解你的感受"、"这确实很难"等共情语言
- 倾听为主，不给太多建议
- 关注用户的情绪状态

❌ 避免的做法
- 避免急于解决问题或提供方案
- 避免过度积极或"正能量"式的鼓励
- 避免轻视用户的困难

✅ 推荐的对话方式
- 温和地探索感受，而不是分析问题
- 确认和接纳用户的情绪
- 表达持续陪伴："我会一直在这里陪着你"
- 可以问："你愿意多跟我说说你的感受吗？"
"""

        elif is_consistent and dominant_emotion == "positive":
            # 持续正面情绪
            return """【当前情绪状态：持续正面】✨

用户最近多次对话呈现积极情绪。

对话策略调整：
✅ 适当强化积极行为
- 庆祝小进步和积极变化
- 肯定用户的努力和勇气
- 强化健康习惯和积极思维

✅ 可以适度探讨未来
- 可以讨论短期目标和计划
- 鼓励保持健康习惯
- 庆疗愈过程中的进步

✅ 推荐的对话方式
- "你做得很好！"
- "这真的是很棒的进步！"
- "你感觉怎么样？继续保持这种感觉的方法有哪些？"
"""

        elif is_consistent and dominant_emotion == "neutral":
            # 持续中性情绪
            return """【当前情绪状态：平稳】

用户最近对话情绪较为平稳中性。

对话策略调整：
✅ 保持温和友好的对话
- 自然对话节奏
- 灵活调整对话策略
- 可以探索更多话题

✅ 开放式问题探索需求
- "今天想聊些什么？"
- "最近有什么想分享的吗？"
- 保持陪伴但不过度引导
"""

        elif latest_emotion == "negative":
            # 最近一次转为负面（情绪波动）
            return """【当前情绪状态：情绪波动 - 近期转为负面】

用户最近的对话情绪出现波动，本次呈现负面情绪。

对话策略调整：
✅ 优先关注当前负面情绪
- 倾听并确认用户的感受
- 探索负面情绪的原因（温和地）
- 提供额外的情感支持

✅ 观察情绪变化
- 注意情绪是否持续恶化
- 必要时引导寻求专业帮助
- 记录情绪变化趋势

✅ 推荐的对话方式
- "我注意到你最近似乎不太开心，愿意跟我说说吗？"
- "这次感觉和之前有什么不同吗？"
"""

        elif latest_emotion == "positive":
            # 最近一次转为正面（情绪改善）
            return """【当前情绪状态：情绪改善 - 近期转为正面】

用户最近的对话情绪出现积极转变！

对话策略调整：
✅ 强化积极转变
- 肯定用户的积极变化
- 探讨什么起了作用
- 鼓励继续保持

✅ 但不过度庆祝
- 保持适度，避免过度兴奋
- 尊重用户的节奏
- 继续保持陪伴

✅ 推荐的对话方式
- "我感觉到你最近状态好了一些，是什么帮助了你？"
- "这种积极的感觉怎么样？"
- "你做得很棒，继续保持！"
"""

        else:
            # 混合情绪状态
            return """【当前情绪状态：情绪起伏】

用户最近的对话情绪呈现起伏状态，混合了多种情绪。

对话策略调整：
✅ 灵活应对
- 根据每次对话的具体情绪调整策略
- 保持敏感和开放
- 不要假设用户状态

✅ 推荐的对话方式
- "你今天感觉怎么样？"
- 灵活跟随用户的情绪线索
- 保持温和友好的陪伴
"""

    def _get_recent_emotions(self, n: int = 3) -> list:
        """
        获取用户最近N次对话的情绪

        Args:
            n: 获取最近N次，默认3次

        Returns:
            情绪列表，如 ["negative", "neutral", "positive"]
        """
        try:
            # 查询最近N条对话消息
            recent_messages = db.session.query(
                ChatMessage.emotion
            ).filter_by(
                user_id=self.user_id
            ).order_by(
                ChatMessage.created_at.desc()
            ).limit(n).all()

            # 提取情绪（按时间正序）
            emotions = [msg.emotion for msg in reversed(recent_messages) if msg.emotion]

            return emotions

        except Exception as e:
            print(f"[动态Prompt] 获取历史情绪失败: {e}")
            return []

    def _get_emotion_adaptation_compact(self) -> str:
        """
        精简版情绪适应（病耻感友好 + 高性能）

        优化点：
        1. 优先关注当前情绪，不过度依赖历史
        2. 控制在30-50字符
        3. 避免指令冲突

        Returns:
            精简的情绪适应字符串
        """
        # 不再过度依赖历史情绪，返回空字符串
        # 让模型更专注于当前输入
        return ""

    def _get_time_adjustment_compact(self) -> str:
        """
        精简版时间段调整（高性能）

        Returns:
            精简的时间调整字符串（20-50字符）
        """
        hour = datetime.now().hour

        # 精简的时间段映射
        if 6 <= hour < 9:
            return "早晨：积极引导，设定今日小目标。"
        elif 9 <= hour < 12:
            return "上午：关注压力感受，提供放松技巧。"
        elif 12 <= hour < 14:
            return "午间：轻松聊天，避免沉重话题。"
        elif 14 <= hour < 18:
            return "下午：鼓励性对话，肯定努力。"
        elif 18 <= hour < 21:
            return "傍晚：提供情绪支持，倾听今日经历。"
        elif 21 <= hour < 24 or 0 <= hour < 1:
            return "深夜：使用极度舒缓语调，避免刺激话题，引导放松。⚠️"
        else:  # 1:00-6:00
            return "凌晨：优先评估安全，提供危机干预资源。⚠️⚠️"

    def _get_safety_constraints_compact(self) -> str:
        """
        精简版安全约束（保留核心）

        Returns:
            精简的安全约束字符串（80-100字符）
        """
        return """⚠️ 安全优先：不做医学诊断，不建议药物。自杀/自伤意念→立即引导就医（热线：400-161-9995）"""

    def _get_time_adjustment(self) -> str:
        """
        根据当前时间段生成对话调整策略

        Returns:
            时间调整字符串
        """
        hour = datetime.now().hour

        # 时间段策略映射
        time_strategies = {
            # 早晨 06:00-09:00
            (6, 9): """【当前时间：早晨】
用户状态：可能刚起床，情绪较积极

对话策略调整：
✅ 积极引导，设定今日小目标
✅ 鼓励健康早餐或晨间习惯
✅ 语调轻快但不过度兴奋
✅ 可以问"今天有什么计划吗？""",

            # 上午 09:00-12:00
            (9, 12): """【当前时间：上午】
用户状态：工作/学习压力可能上升

对话策略调整：
✅ 关注压力感受
✅ 提供压力管理技巧
✅ 适度鼓励，避免施压
✅ 可以问"最近工作/学习怎么样？""",

            # 午间 12:00-14:00
            (12, 14): """【当前时间：午间】
用户状态：午休时段，相对放松

对话策略调整：
✅ 轻松话题，可以闲聊日常
✅ 避免沉重话题
✅ 可以聊"午餐怎么样？""",

            # 下午 14:00-18:00
            (14, 18): """【当前时间：下午】
用户状态：下午疲劳期

对话策略调整：
✅ 鼓励性对话
✅ 适度肯定用户努力
✅ 避免复杂问题
✅ 可以问"累了吗？休息一下""",

            # 傍晚 18:00-21:00
            (18, 21): """【当前时间：傍晚】
用户状态：情绪波动高峰期

对话策略调整：
✅ 提供情绪支持
✅ 倾听今日经历
✅ 共情为主，减少建议
✅ 可以问"今天过得怎么样？""",

            # 深夜 21:00-01:00
            (21, 1): """【当前时间：深夜】⚠️ 高敏感时段
用户状态：情绪可能脆弱，准备休息

⚠️ 重要调整：
✅ 使用极度舒缓、温和的语调
✅ 多使用安抚性语言（"慢慢来"、"没关系"、"我在这里"）
❌ 避免讨论刺激性话题
❌ 不建议进行深度反思或问题解决
✅ 可以引导放松和积极想象
✅ 如果失眠，提供放松技巧

禁用话题：
- ❌ 不讨论压力源
- ❌ 不分析问题根源
- ❌ 不设定行动目标
- ❌ 不询问复杂问题

推荐话题：
- ✅ 感受确认（"我理解你的感受"）
- ✅ 放松引导（"深呼吸..."）
- ✅ 积极回忆（"今天有什么小确幸吗？"）""",

            # 凌晨 01:00-06:00
            (1, 6): """【当前时间：凌晨】⚠️⚠️ 高危时段
用户状态：深夜活跃，可能高危

⚠️ 危机干预优先：
1. 优先评估安全状态
2. 如果表达绝望/自杀意念 → 立即引导就医
3. 提供危机干预资源
4. 避免深层对话
5. 引导寻求专业帮助

对话策略：
- 温和询问："这个时候还没睡，是因为什么吗？"
- 如果情绪低落："你愿意跟我说说发生了什么吗？"
- 如果表达绝望："我很担心你的安全，请联系专业帮助"
- 提供资源："心理援助热线：400-161-9995"
"""
        }

        # 查找匹配的时间段
        for (start_hour, end_hour), strategy in time_strategies.items():
            if start_hour <= hour < end_hour or (start_hour > end_hour and (hour >= start_hour or hour < end_hour)):
                return strategy

        # 默认策略（不应该到达这里）
        return "【当前时间：白天】\n对话策略：自然对话，关注用户需求"

    def _get_safety_constraints(self) -> str:
        """
        获取安全约束（始终包含）

        Returns:
            安全约束字符串
        """
        return """【安全约束】

❌ 禁止事项：
- 不做医学诊断
- 不建议药物
- 不替代专业治疗
- 不提供医学治疗建议

⚠️ 危机干预：
- 如果用户表达自杀/自伤意念 → 立即引导就医
- 如果用户表达伤害他人意念 → 立即引导就医
- 如果用户长期失眠/食欲改变 → 建议专业咨询
- 如果用户表达绝望感 → 提供专业资源

📞 推荐资源：
- 全国心理援助热线：400-161-9995
- 北京心理危机研究与干预中心：010-82951332
- 上海心理援助热线：021-12320-5

💡 始终强调：
"我是一个AI陪伴助手，不能替代专业心理治疗。
如果你感到非常痛苦，我强烈建议寻求专业心理咨询师的帮助。" """

    def get_depression_level(self) -> str:
        """
        获取当前用户的抑郁程度

        Returns:
            抑郁程度字符串
        """
        if self.strategy_profile and self.strategy_profile.depression_level:
            return self.strategy_profile.depression_level
        return "mild"  # 默认轻度

    def get_current_time_period(self) -> Dict:
        """
        获取当前时间段信息

        Returns:
            {
                "hour": 14,
                "period": "afternoon",
                "period_name": "下午",
                "is_night": False,
                "is_high_risk": False
            }
        """
        hour = datetime.now().hour

        # 判断时间段
        if 6 <= hour < 9:
            period = "morning"
            period_name = "早晨"
            is_night = False
            is_high_risk = False
        elif 9 <= hour < 12:
            period = "late_morning"
            period_name = "上午"
            is_night = False
            is_high_risk = False
        elif 12 <= hour < 14:
            period = "noon"
            period_name = "午间"
            is_night = False
            is_high_risk = False
        elif 14 <= hour < 18:
            period = "afternoon"
            period_name = "下午"
            is_night = False
            is_high_risk = False
        elif 18 <= hour < 21:
            period = "evening"
            period_name = "傍晚"
            is_night = False
            is_high_risk = False
        elif 21 <= hour < 24 or 0 <= hour < 1:
            period = "night"
            period_name = "深夜"
            is_night = True
            is_high_risk = True
        else:  # 1:00-6:00
            period = "midnight"
            period_name = "凌晨"
            is_night = True
            is_high_risk = True

        return {
            "hour": hour,
            "period": period,
            "period_name": period_name,
            "is_night": is_night,
            "is_high_risk": is_high_risk
        }

    def get_emotion_context(self) -> Dict:
        """
        获取用户情绪状态上下文

        Returns:
            {
                "recent_emotions": ["negative", "negative", "neutral"],
                "dominant_emotion": "negative",
                "latest_emotion": "neutral",
                "is_consistent": false,
                "emotion_state": "fluctuating"
            }
        """
        # 获取最近3次情绪
        recent_emotions = self._get_recent_emotions(n=3)

        if not recent_emotions:
            return {
                "recent_emotions": [],
                "dominant_emotion": None,
                "latest_emotion": None,
                "is_consistent": False,
                "emotion_state": "unknown",
                "state_description": "无历史情绪数据"
            }

        # 分析情绪分布
        from collections import Counter
        emotion_counts = Counter(recent_emotions)

        # 主导情绪
        dominant_emotion = emotion_counts.most_common(1)[0][0]
        dominant_count = emotion_counts[dominant_emotion]
        total_count = len(recent_emotions)

        # 判断一致性
        is_consistent = dominant_count == total_count

        # 最近一次情绪
        latest_emotion = recent_emotions[-1]

        # 判断情绪状态
        if is_consistent and dominant_emotion == "negative":
            emotion_state = "consistently_negative"
            state_description = "持续负面"
        elif is_consistent and dominant_emotion == "positive":
            emotion_state = "consistently_positive"
            state_description = "持续正面"
        elif is_consistent and dominant_emotion == "neutral":
            emotion_state = "stable"
            state_description = "平稳中性"
        elif latest_emotion == "negative":
            emotion_state = "fluctuating_to_negative"
            state_description = "情绪波动（转负）"
        elif latest_emotion == "positive":
            emotion_state = "improving"
            state_description = "情绪改善"
        else:
            emotion_state = "fluctuating"
            state_description = "情绪起伏"

        return {
            "recent_emotions": recent_emotions,
            "dominant_emotion": dominant_emotion,
            "latest_emotion": latest_emotion,
            "is_consistent": is_consistent,
            "emotion_state": emotion_state,
            "state_description": state_description
        }


# ==================== 便捷函数 ====================

def generate_prompt_for_user(user_id: int) -> str:
    """
    为指定用户生成动态prompt（便捷函数）

    Args:
        user_id: 用户ID

    Returns:
        生成的system prompt
    """
    generator = DynamicPromptGenerator(user_id)
    return generator.generate_system_prompt()


def get_user_context(user_id: int) -> Dict:
    """
    获取用户上下文信息（用于调试）

    阶段2更新：加入情绪状态上下文

    Args:
        user_id: 用户ID

    Returns:
        用户上下文字典
    """
    generator = DynamicPromptGenerator(user_id)

    return {
        "user_id": user_id,
        "depression_level": generator.get_depression_level(),
        "time_context": generator.get_current_time_period(),
        "emotion_context": generator.get_emotion_context()  # 阶段2新增
    }


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 70)
    print("动态Prompt生成系统 - 阶段1测试".center(70))
    print("=" * 70)

    # 测试不同抑郁程度
    test_cases = [
        {"user_id": 1, "depression_level": "minimal"},
        {"user_id": 2, "depression_level": "mild"},
        {"user_id": 3, "depression_level": "moderate"},
        {"user_id": 4, "depression_level": "moderately_severe"},
        {"user_id": 5, "depression_level": "severe"},
    ]

    print("\n【测试1】不同抑郁程度的Prompt对比\n")
    print("-" * 70)

    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {case['depression_level']}抑郁")
        print(f"用户ID: {case['user_id']}")

        # 生成prompt
        try:
            generator = DynamicPromptGenerator(case['user_id'])
            prompt = generator.generate_system_prompt()

            print(f"\n生成的Prompt预览（前300字）:")
            print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
            print(f"\n完整Prompt长度: {len(prompt)} 字符")

        except Exception as e:
            print(f"生成失败: {e}")

        print("-" * 70)

    # 测试时间调整
    print("\n【测试2】当前时间段上下文\n")
    print("-" * 70)

    try:
        user_id = 1
        context = get_user_context(user_id)

        print(f"用户ID: {user_id}")
        print(f"抑郁程度: {context['depression_level']}")
        print(f"\n时间上下文:")
        print(f"  当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  时段: {context['time_context']['period_name']}")
        print(f"  是否深夜: {'是' if context['time_context']['is_night'] else '否'}")
        print(f"  是否高危: {'是⚠️' if context['time_context']['is_high_risk'] else '否'}")

    except Exception as e:
        print(f"获取上下文失败: {e}")

    print("\n" + "=" * 70)
    print("测试完成！".center(70))
    print("=" * 70)
