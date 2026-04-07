"""
MindChat 对话系统 - 精简版
固定 prompt，不依赖历史，不使用个性化策略
"""

from mindchat_model import MindChatDialogue
from typing import Dict, Optional


class IntegratedMindChatSystem:
    """集成的 MindChat 对话系统 - 精简版"""

    # 用户请求关键词识别
    MEDIA_REQUEST_KEYWORDS = {
        "music": ["音乐", "歌", "听歌", "播放音乐", "来首音乐", "唱首歌", "音乐疗愈", "轻音乐", "舒缓音乐"],
        "video": ["视频", "看视频", "播放视频", "动画", "看动画", "视频疗愈"],
        "both": ["放松", "疗愈", "舒缓", "安慰", "治愈", "陪伴", "休息一下"]
    }

    def __init__(
        self,
        sentiment_model_path: Optional[str] = None,
        mindchat_model_path: str = "./models/qwen2-1.5b-instruct/Qwen/qwen2-1.5b-instruct",
        load_in_4bit: bool = False,
        user_id: Optional[int] = None,
    ):
        """
        初始化 MindChat 对话系统

        Args:
            sentiment_model_path: 情绪分析模型路径（未使用）
            mindchat_model_path: MindChat 模型路径
            load_in_4bit: 未使用参数
            user_id: 未使用参数（保留接口兼容性）
        """
        self.mindchat = MindChatDialogue(model_path=mindchat_model_path)

    def analyze_and_respond(self, user_input: str, system_prompt: Optional[str] = None, user_id: Optional[int] = None) -> Dict:
        """
        分析用户输入并生成响应

        Args:
            user_input: 用户输入文本
            system_prompt: 自定义system prompt（可选）
            user_id: 用户ID（保留接口兼容性）

        Returns:
            包含响应和引导问题的字典
        """
        try:
            # 调用模型生成回复（不使用历史）
            response = self.mindchat.chat(user_input, system_prompt=system_prompt, user_id=None)

            # 生成引导问题
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

        Args:
            user_input: 用户输入
            response: 模型回复

        Returns:
            引导问题列表
        """
        questions = []

        # 基于AI回复内容生成用户可能的回应
        if any(method in response for method in ["深呼吸", "冥想", "运动", "瑜伽", "散步", "休息"]):
            questions.append("我想试试这个方法")
            questions.append("还有其他放松方法吗")
            if "深呼吸" in response:
                questions.append("教我怎么深呼吸")
        elif any(word in response for word in ["睡眠", "失眠", "作息", "睡前"]):
            questions.append("我最近总是失眠")
            questions.append("睡前怎么放松比较好")
            questions.append("有什么助眠的方法吗")
        elif any(word in response for word in ["建议", "可以尝试", "试试看", "可以帮助"]):
            questions.append("这个建议听起来不错")
            questions.append("我试试看")
            questions.append("还有什么其他建议吗")
        else:
            # 根据用户输入的主题生成用户可能的回应
            if any(word in user_input for word in ["压力", "累", "疲惫", "紧张", "辛苦"]):
                questions.append("工作压力特别大")
                questions.append("最近事情太多了")
                questions.append("感觉喘不过气来")
            elif any(word in user_input for word in ["焦虑", "担心", "不安", "害怕"]):
                questions.append("我最近总是胡思乱想")
                questions.append("对未来很迷茫")
                questions.append("控制不住担心")
            elif any(word in user_input for word in ["难过", "伤心", "痛苦", "难受"]):
                questions.append("发生了一些不愉快的事")
                questions.append("心里堵得慌")
                questions.append("想找个地方倾诉")
            elif any(word in user_input for word in ["失眠", "睡不着", "睡眠"]):
                questions.append("每晚都睡不着")
                questions.append("凌晨就醒了")
                questions.append("睡前总是想很多")
            elif any(word in user_input for word in ["工作", "学习", "考试", "项目"]):
                questions.append("任务太重了")
                questions.append("不知道怎么安排时间")
                questions.append("感觉很无力")
            elif any(word in user_input for word in ["朋友", "家人", "同事", "人际", "孤独"]):
                questions.append("感觉没人理解我")
                questions.append("不知道怎么和人相处")
                questions.append("想找人说说话")
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

        return questions[:3]

    def chat(self, message: str, sentiment_context: Optional[Dict] = None) -> str:
        """
        进行对话

        Args:
            message: 用户消息
            sentiment_context: 情绪上下文（未使用）

        Returns:
            响应文本
        """
        return self.mindchat.chat(message)

    def clear_history(self, user_id: Optional[int] = None):
        """
        清除对话历史（空操作，因为不使用历史）

        Args:
            user_id: 用户ID
        """
        pass

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
                result["music"] = True
                result["video"] = True
                break

        return result

    def set_user_id(self, user_id: int):
        """设置用户ID（空操作，保留接口兼容性）"""
        pass

    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        生成响应（用于危机干预等场景）

        Args:
            prompt: 提示文本
            context: 上下文信息（未使用）

        Returns:
            生成的响应文本
        """
        return self.mindchat.chat(prompt)
