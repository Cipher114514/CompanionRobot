"""危机检测核心逻辑"""

import json
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

from .config import CrisisConfig
from .bridges import EmotionBridge, VoiceBridge


@dataclass
class CrisisDetectionResult:
    """检测结果"""
    is_crisis: bool = False
    level: int = 0                    # 0-3级
    confidence: float = 0.0
    keywords: list = field(default_factory=list)
    sources: dict = field(default_factory=dict)
    suggested_action: str = ""
    detected_at: datetime = field(default_factory=datetime.now)


class CrisisDetector:
    """危机检测器"""
    
    def __init__(self, config: Optional[CrisisConfig] = None):
        self.config = config or CrisisConfig.load()
        self.keywords_data = self._load_keywords()
        # 桥接模块可选初始化（避免模块不存在时报错）
        self.emotion_bridge = EmotionBridge()
        self.voice_bridge = VoiceBridge()
    
    def _load_keywords(self) -> dict:
        """加载危机词库"""
        try:
            with open(self.config.KEYWORDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self._get_default_keywords()
    
    def _get_default_keywords(self) -> dict:
        """默认词库（文件加载失败时使用）"""
        return {
            "high": ["自杀", "自尽", "轻生", "不想活了", "结束生命"],
            "medium": ["伤害自己", "割腕", "吃药", "太累了", "撑不下去"],
            "low": ["难过", "痛苦", "绝望", "没意义", "好累"]
        }
    
    def detect(
        self,
        user_input: str,
        user_id: int,
        voice_emotion: Optional[str] = None,
        scale_scores: Optional[dict] = None,
    ) -> CrisisDetectionResult:
        """执行危机检测 - 融合文本、语音、量表多维度信息"""
        result = CrisisDetectionResult()
        result.sources = {"text": False, "voice": False, "scale": False}
        
        # 1. 文本关键词检测
        if self.config.ENABLE_TEXT_DETECTION:
            text_keywords, _ = self._detect_text(user_input)
            result.keywords.extend(text_keywords)
            result.sources["text"] = len(text_keywords) > 0
        
        # 2. 语音情绪检测
        if self.config.ENABLE_VOICE_DETECTION and voice_emotion:
            voice_score = self._detect_voice(voice_emotion)
            result.sources["voice"] = voice_score > 0.3
        
        # 3. 量表分数检测（已禁用）
        if self.config.ENABLE_SCALE_DETECTION:
            # 量表功能已移除，不再执行量表检测
            scale_score = 0.0
        
        # 4. 情绪分析辅助
        try:
            emotion = self.emotion_bridge.get_emotion(user_id, user_input)
            emotion_boost = self._get_emotion_boost(emotion)
        except Exception as e:
            print(f"情绪分析失败：{e}")
            emotion_boost = 0.0
        
        # 5. 综合置信度计算
        base_score = self._calculate_keyword_score(result.keywords)
        result.confidence = min(1.0, base_score + emotion_boost)
        
        # 6. 判定危机等级
        result.level = self._classify_level(result.confidence, result.keywords)
        result.is_crisis = result.level >= 1
        
        # 7. 生成建议行动
        result.suggested_action = self._get_suggested_action(result.level)
        
        return result
    
    def _detect_text(self, text: str) -> tuple[list, float]:
        """文本关键词检测"""
        matched = []
        for level, words in self.keywords_data.items():
            for word in words:
                if word in text:
                    matched.append(word)
        
        score = len(matched) * 0.2
        return matched, min(1.0, score)
    
    def _detect_voice(self, emotion: str) -> float:
        """语音情绪检测"""
        negative_emotions = self.config.VOICE_NEGATIVE_EMOTIONS
        return self.config.VOICE_NEGATIVE_SCORE if emotion in negative_emotions else self.config.VOICE_NEUTRAL_SCORE
    
    def _detect_scale(self, scores: dict) -> float:
        """
        量表分数检测（已废弃）

        注意：量表功能已移除，此方法保留仅为向后兼容
        实际不会被调用（ENABLE_SCALE_DETECTION = False）
        """
        phq9 = scores.get("PHQ-9", 0)
        # 注意：PHQ9_WARNING_SCORE和PHQ9_CRITICAL_SCORE配置已移除
        # 此处使用硬编码的默认值
        if phq9 >= 20:  # PHQ9_CRITICAL_SCORE
            return 0.9
        elif phq9 >= 10:  # PHQ9_WARNING_SCORE
            return 0.5
        return 0.1
    
    def _get_emotion_boost(self, emotion: Optional[str]) -> float:
        """情绪分析增益"""
        if emotion in ["depressed", "anxious"]:
            return 0.15
        elif emotion == "negative":
            return 0.1
        return 0.0
    
    def _calculate_keyword_score(self, keywords: list) -> float:
        """计算关键词得分"""
        score = 0.0
        for word in keywords:
            if word in self.keywords_data.get("high", []):
                score += 0.4
            elif word in self.keywords_data.get("medium", []):
                score += 0.25
            elif word in self.keywords_data.get("low", []):
                score += 0.15
        return min(1.0, score)
    
    def _classify_level(self, confidence: float, keywords: list) -> int:
        """判定危机等级"""
        has_high = any(w in self.keywords_data.get("high", []) for w in keywords)
        
        if has_high or confidence >= self.config.LEVEL_3_THRESHOLD:
            return 3
        elif confidence >= self.config.LEVEL_2_THRESHOLD:
            return 2
        elif confidence >= self.config.LEVEL_1_THRESHOLD:
            return 1
        return 0
    
    def _get_suggested_action(self, level: int) -> str:
        """获取建议行动"""
        actions = {
            0: "继续陪伴观察",
            1: "温暖关怀，推荐疗愈内容",
            2: "建议专业心理咨询",
            3: "强烈建议立即联系专业机构"
        }
        return actions.get(level, "继续陪伴观察")
    
    def should_interrupt(self, result: CrisisDetectionResult) -> bool:
        """判断是否需要中断正常对话（2级及以上）"""
        return result.level >= 2