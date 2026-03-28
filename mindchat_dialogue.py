"""
MindChat 对话系统
"""

from mindchat_model import MindChatDialogue
from typing import Dict, Optional
from models import db, UserStrategyProfile, StrategyUsageLog


class IntegratedMindChatSystem:
    """集成的 MindChat 对话系统 - 增强主动性"""

    # 用户请求关键词识别
    MEDIA_REQUEST_KEYWORDS = {
        "music": ["音乐", "歌", "听歌", "播放音乐", "来首音乐", "唱首歌", "音乐疗愈", "轻音乐", "舒缓音乐"],
        "video": ["视频", "看视频", "播放视频", "动画", "看动画", "视频疗愈"],
        "both": ["放松", "疗愈", "舒缓", "安慰", "治愈", "陪伴", "休息一下"]
    }

    def __init__(
        self,
        sentiment_model_path: Optional[str] = None,
        mindchat_model_path: str = "./models/qwen2-1.5b-instruct/Qwen/qwen2-1___5b-instruct",
        load_in_4bit: bool = False,
        user_id: Optional[int] = None,
    ):
        """
        初始化 MindChat 对话系统

        Args:
            sentiment_model_path: 情绪分析模型路径（可选）
            mindchat_model_path: MindChat 模型路径
            load_in_4bit: 是否使用 4-bit 量化（未使用）
            user_id: 用户ID（用于个性化策略）
        """
        self.mindchat = MindChatDialogue(model_path=mindchat_model_path)
        self.user_id = user_id
        self.current_strategy = None  # 当前使用的策略

    def analyze_and_respond(self, user_input: str, system_prompt: Optional[str] = None, user_id: Optional[int] = None) -> Dict:
        """
        分析用户输入并生成响应

        Args:
            user_input: 用户输入文本
            system_prompt: 自定义system prompt（可选）
            user_id: 用户ID（可选，用于隔离对话历史）

        Returns:
            包含响应和引导问题的字典
        """
        try:
            # 使用实例的user_id或传入的user_id
            effective_user_id = user_id if user_id is not None else self.user_id

            # 调用模型生成回复（传入user_id）
            response = self.mindchat.chat(user_input, system_prompt=system_prompt, user_id=effective_user_id)

            # 使用预设模板生成引导问题
            follow_up_questions = self._generate_follow_up_questions(user_input, response)

            return {
                "success": True,
                "response": response,
                "input": user_input,
                "system_prompt_used": system_prompt,
                "follow_up_questions": follow_up_questions
            }
        except Exception as e:
            return {
                "success": False,
                "response": f"抱歉，对话生成出现问题：{str(e)}",
                "error": str(e),
                "follow_up_questions": []
            }

    def _generate_follow_up_questions(self, user_input: str, response: str) -> list:
        """
        根据用户输入和AI回复生成引导问题

        引导问题的本质：帮助用户快速输入（用户视角的快捷回复）
        而不是：AI想要问用户的问题

        Args:
            user_input: 用户输入
            response: 模型回复

        Returns:
            引导问题列表（用户可能的输入）
        """
        questions = []

        # 基于AI回复内容生成用户可能的回应
        # 1. AI提到了具体的放松方法
        if any(method in response for method in ["深呼吸", "冥想", "运动", "瑜伽", "散步", "休息"]):
            questions.append("我想试试这个方法")
            questions.append("还有其他放松方法吗")

            # 如果提到了深呼吸
            if "深呼吸" in response:
                questions.append("教我怎么深呼吸")

        # 2. AI提到了睡眠建议
        elif any(word in response for word in ["睡眠", "失眠", "作息", "睡前"]):
            questions.append("我最近总是失眠")
            questions.append("睡前怎么放松比较好")
            questions.append("有什么助眠的方法吗")

        # 3. AI给出了建议或方法
        elif any(word in response for word in ["建议", "可以尝试", "试试看", "可以帮助"]):
            questions.append("这个建议听起来不错")
            questions.append("我试试看")
            questions.append("还有什么其他建议吗")

        # 4. 如果AI没有明确建议，基于用户输入的主题生成用户可能的回应
        else:
            # 压力/紧张相关 - 用户可能的分享
            if any(word in user_input for word in ["压力", "累", "疲惫", "紧张", "辛苦"]):
                questions.append("工作压力特别大")
                questions.append("最近事情太多了")
                questions.append("感觉喘不过气来")

            # 焦虑/担心相关 - 用户可能的分享
            elif any(word in user_input for word in ["焦虑", "担心", "不安", "害怕"]):
                questions.append("我最近总是胡思乱想")
                questions.append("对未来很迷茫")
                questions.append("控制不住担心")

            # 难过/伤心相关 - 用户可能的分享
            elif any(word in user_input for word in ["难过", "伤心", "痛苦", "难受"]):
                questions.append("发生了一些不愉快的事")
                questions.append("心里堵得慌")
                questions.append("想找个地方倾诉")

            # 失眠相关 - 用户可能的分享
            elif any(word in user_input for word in ["失眠", "睡不着", "睡眠"]):
                questions.append("每晚都睡不着")
                questions.append("凌晨就醒了")
                questions.append("睡前总是想很多")

            # 工作/学习相关 - 用户可能的分享
            elif any(word in user_input for word in ["工作", "学习", "考试", "项目"]):
                questions.append("任务太重了")
                questions.append("不知道怎么安排时间")
                questions.append("感觉很无力")

            # 人际相关 - 用户可能的分享
            elif any(word in user_input for word in ["朋友", "家人", "同事", "人际", "孤独"]):
                questions.append("感觉没人理解我")
                questions.append("不知道怎么和人相处")
                questions.append("想找人说说话")

            # 通用用户可能的回应
            else:
                questions.append("能给我一些建议吗")
                questions.append("我只是想找人说说话")
                questions.append("不知道该怎么办")

        # 如果没有生成足够问题，添加通用选项
        if len(questions) < 3:
            remaining = 3 - len(questions)
            generic_questions = [
                "能给我一些建议吗",
                "我想了解更多",
                "不知道该怎么说"
            ]
            questions.extend(generic_questions[:remaining])

        # 最多返回3个问题
        return questions[:3]

    def chat(self, message: str, sentiment_context: Optional[Dict] = None) -> str:
        """
        进行对话

        Args:
            message: 用户消息
            sentiment_context: 情绪上下文（可选）

        Returns:
            响应文本
        """
        return self.mindchat.chat(message, sentiment_context)

    def clear_history(self, user_id: Optional[int] = None):
        """
        清除对话历史

        Args:
            user_id: 要清除的用户ID，如果为None则清除当前用户的历史
        """
        effective_user_id = user_id if user_id is not None else self.user_id
        self.mindchat.clear_history(effective_user_id)

    def detect_media_request(self, user_input: str) -> Dict[str, bool]:
        """
        检测用户是否请求音乐或视频

        Args:
            user_input: 用户输入

        Returns:
            {"music": bool, "video": bool}
        """
        user_input_lower = user_input.lower()
        result = {"music": False, "video": False}

        # 检查音乐请求
        for keyword in self.MEDIA_REQUEST_KEYWORDS["music"]:
            if keyword in user_input_lower:
                result["music"] = True
                break

        # 检查视频请求
        for keyword in self.MEDIA_REQUEST_KEYWORDS["video"]:
            if keyword in user_input_lower:
                result["video"] = True
                break

        # 检查通用疗愈请求
        for keyword in self.MEDIA_REQUEST_KEYWORDS["both"]:
            if keyword in user_input_lower:
                # 根据上下文判断，这里两个都返回 True
                result["music"] = True
                result["video"] = True
                break

        return result

    def suggest_healing_media(self, emotion: str = "neutral") -> Dict[str, str]:
        """
        根据情绪主动建议疗愈媒体

        Args:
            emotion: 检测到的情绪 (positive, negative, neutral)

        Returns:
            建议字典 {"should_suggest": bool, "type": str, "message": str}
        """
        suggestions = {
            "negative": {
                "should_suggest": True,
                "type": "both",
                "message": "我感觉到你可能需要一些舒缓。我可以为你生成一段疗愈音乐或安慰性的视频来帮助你放松。需要吗？"
            },
            "neutral": {
                "should_suggest": False,
                "type": "",
                "message": ""
            },
            "positive": {
                "should_suggest": False,
                "type": "",
                "message": ""
            }
        }

        return suggestions.get(emotion, suggestions["neutral"])

    def analyze_and_respond_with_suggestions(
        self,
        user_input: str,
        emotion: Optional[str] = None,
        emotion_confidence: float = 0.0
    ) -> Dict:
        """
        分析用户输入并生成响应（增强版 - 包含媒体建议）

        Args:
            user_input: 用户输入文本
            emotion: 检测到的情绪（可选）
            emotion_confidence: 情绪置信度

        Returns:
            包含响应和建议的字典
        """
        # 1. 检测用户主动请求
        media_request = self.detect_media_request(user_input)

        # 2. 获取 AI 回复
        response = self.mindchat.chat(user_input)

        # 3. 根据情绪决定是否主动建议
        should_suggest_media = False
        suggestion_type = ""
        suggestion_message = ""

        if emotion and emotion_confidence > 0.7:  # 只在置信度高时主动建议
            suggestion = self.suggest_healing_media(emotion)
            should_suggest_media = suggestion["should_suggest"]
            suggestion_type = suggestion["type"]
            suggestion_message = suggestion["message"]

        return {
            "success": True,
            "response": response,
            "input": user_input,
            # 用户请求检测
            "user_requests_music": media_request["music"],
            "user_requests_video": media_request["video"],
            # 主动建议
            "should_suggest_media": should_suggest_media,
            "suggestion_type": suggestion_type,
            "suggestion_message": suggestion_message,
            # 情绪信息
            "detected_emotion": emotion,
            "emotion_confidence": emotion_confidence
        }

    def load_personalized_strategy(self) -> Optional[Dict]:
        """
        加载用户的个性化疗愈策略

        Returns:
            策略字典，如果用户未设置则返回 None
        """
        if not self.user_id:
            return None

        try:
            from personalized_healing import StrategyRecommender

            recommender = StrategyRecommender(self.user_id)
            strategy_report = recommender.generate_strategy_report()

            # 提取对话策略
            conversation_strategy = strategy_report.get("conversation_strategy", {})
            self.current_strategy = conversation_strategy

            return conversation_strategy

        except Exception as e:
            print(f"加载个性化策略失败: {e}")
            return None

    def get_system_prompt(self) -> str:
        """
        获取当前对话风格的 system prompt

        Returns:
            system prompt 字符串
        """
        # 如果有个性化策略，使用个性化 prompt
        if self.current_strategy:
            return self.current_strategy.get("system_prompt", "")

        # 否则使用默认的温和共情 prompt
        return """你是一位温暖、专业的心理咨询师。
你的特点：
- 倾听为主，给予情感支持
- 语言温柔、舒缓
- 关注用户的情绪状态
- 不轻易下判断，多理解和共情
"""

    def chat_with_strategy(
        self,
        message: str,
        emotion: Optional[str] = None,
        emotion_confidence: float = 0.0
    ) -> Dict:
        """
        使用个性化策略进行对话

        Args:
            message: 用户消息
            emotion: 检测到的情绪（可选）
            emotion_confidence: 情绪置信度

        Returns:
            包含响应和策略信息的字典
        """
        # 加载个性化策略
        strategy = self.load_personalized_strategy()

        # 获取 system prompt
        system_prompt = self.get_system_prompt()

        # TODO: 这里需要修改 UltraFastMindChatDialogue 来支持自定义 system prompt
        # 目前先用普通方式调用
        response = self.mindchat.chat(message)

        return {
            "success": True,
            "response": response,
            "input": message,
            "strategy_used": strategy.get("style_id") if strategy else "default",
            "strategy_name": strategy.get("style_name") if strategy else "默认",
            "detected_emotion": emotion,
            "emotion_confidence": emotion_confidence
        }

    def set_user_id(self, user_id: int):
        """设置用户ID（用于切换用户）"""
        self.user_id = user_id
        self.current_strategy = None  # 重置策略

    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        生成响应（用于危机干预等场景）

        Args:
            prompt: 提示文本
            context: 上下文信息（可选）

        Returns:
            生成的响应文本
        """
        system_prompt = None
        if context and context.get("user_id"):
            # 如果有用户信息，加载个性化策略
            old_user_id = self.user_id
            self.user_id = context["user_id"]
            strategy = self.load_personalized_strategy()
            self.user_id = old_user_id

            if strategy:
                system_prompt = strategy.get("system_prompt")

        return self.mindchat.chat(prompt, system_prompt=system_prompt)
