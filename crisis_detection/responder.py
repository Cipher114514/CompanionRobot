"""干预话术 - 支持AI动态生成"""

import json
import random
from typing import Optional, Callable
from dataclasses import dataclass, field

from .config import CrisisConfig


@dataclass
class InterventionResponse:
    """干预回复"""
    content: str = ""
    resources: list = field(default_factory=list)
    should_cover: bool = False
    follow_up: Optional[str] = None
    is_ai_generated: bool = False


class CrisisResponder:
    """危机响应生成器"""
    
    def __init__(
        self,
        config: Optional[CrisisConfig] = None,
        ai_generator: Optional[Callable] = None
    ):
        self.config = config or CrisisConfig.load()
        self.ai_generator = ai_generator
        self.responses_data = self._load_responses()
        self.resources_data = self._load_resources()
    
    def _load_responses(self) -> dict:
        """加载预设话术（作为fallback）"""
        try:
            with open(self.config.RESPONSES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self._get_minimal_responses()
    
    def _get_minimal_responses(self) -> dict:
        """最小化预设话术（仅fallback用）"""
        return {
            "level_1": ["我在这里陪着你，想说什么都可以。"],
            "level_2": ["我很关心你的状态，或许可以找专业老师聊聊？"],
            "level_3": ["我很担心你。请考虑联系专业帮助，你不需要一个人承受。"]
        }
    
    def _load_resources(self) -> list:
        """加载转介资源"""
        try:
            with open(self.config.RESOURCES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if self.config.ENABLE_RESOURCES else []
        except Exception:
            return []
    
    def generate(
        self,
        level: int,
        keywords: Optional[list] = None,
        emotion: Optional[str] = None,
        user_input: Optional[str] = None,
        user_context: Optional[dict] = None
    ) -> InterventionResponse:
        """生成干预话术 - 优先AI，fallback到模板"""
        response = InterventionResponse()
        
        # 1. 尝试AI动态生成
        if self.ai_generator and self.config.USE_AI_GENERATION:
            try:
                response.content = self._generate_by_ai(
                    level=level,
                    keywords=keywords,
                    emotion=emotion,
                    user_input=user_input,
                    user_context=user_context
                )
                response.is_ai_generated = True
            except Exception as e:
                print(f"AI生成失败，使用模板：{e}")
                response.content = self._generate_by_template(level, emotion)
        else:
            response.content = self._generate_by_template(level, emotion)
        
        # 2. 根据等级决定是否覆盖正常回复
        response.should_cover = level >= 2
        
        # 3. 添加转介资源
        if level >= 2 and self.config.ENABLE_RESOURCES:
            response.resources = self._select_resources(level)
            if response.resources:
                response.content += self._format_resources(response.resources)
        
        # 4. 后续跟进建议
        response.follow_up = self._get_follow_up(level)
        
        return response
    
    def _generate_by_ai(self, level: int, keywords: Optional[list] = None,
                        emotion: Optional[str] = None, user_input: Optional[str] = None,
                        user_context: Optional[dict] = None) -> str:
        """使用AI动态生成干预话术"""
        prompt = f"""
你是一个温暖的心理陪伴助手。用户可能处于心理困扰中。

【用户输入】{user_input or "无"}
【用户情绪】{emotion or "未知"}

【回应要求】
1. {self._get_level_guidance(level)}
2. 语言温暖自然，像朋友而非机器
3. 不要说"检测到"、"分析"这类机械话
4. 不要强制用户，保留选择权
5. 长度50-150字
6. 延续对话，不要终结

请生成回应：
"""
        if self.ai_generator:
            content = self.ai_generator(prompt, user_context or {})
            return content.strip()
        return self._generate_by_template(level, emotion)
    
    def _get_level_guidance(self, level: int) -> str:
        """获取等级对应的回应指导"""
        guidances = {
            1: "关注用户情绪，给予陪伴支持",
            2: "温和建议可以考虑和专业人士聊聊",
            3: "表达担忧，提供专业帮助资源信息"
        }
        return f"【当前重点】{guidances.get(level, '给予关怀')}"
    
    def _generate_by_template(self, level: int, emotion: Optional[str] = None) -> str:
        """使用预设模板生成（fallback）"""
        template_key = f"level_{level}"
        templates = self.responses_data.get(template_key, 
                                            self.responses_data.get("level_1", []))
        content = random.choice(templates) if templates else "我在这里陪着你。"
        
        # 根据情绪微调
        if emotion:
            adjustments = {
                "depressed": "\n\n我知道现在可能很难，但请相信情况会好转的。",
                "anxious": "\n\n深呼吸，慢慢来，我在这里陪着你。",
                "sad": "\n\n你的感受很重要，我愿意听你说。"
            }
            content += adjustments.get(emotion, "")
        
        return content
    
    def _select_resources(self, level: int) -> list:
        """选择转介资源"""
        if not self.resources_data:
            return []
        return self.resources_data[:2] if level == 3 else self.resources_data[:3]
    
    def _format_resources(self, resources: list) -> str:
        """格式化资源列表"""
        if not resources:
            return ""
        lines = ["\n\n如果你愿意，可以联系以下专业支持："]
        for r in resources:
            name = r.get('name', '')
            contact = r.get('contact', '')
            r_type = r.get('type', '热线')
            lines.append(f"• {name}（{r_type}）: {contact}")
        return "\n".join(lines)
    
    def _get_follow_up(self, level: int) -> Optional[str]:
        """获取后续跟进建议（内部使用）"""
        return {
            1: "稍后跟进情绪状态",
            2: "24小时内关注用户",
            3: "持续监测，必要时提醒"
        }.get(level)