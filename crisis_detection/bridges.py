"""与现有模块的桥接接口"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmotionBridge:
    """情绪分析模块桥接"""
    
    @staticmethod
    def get_emotion(user_id: int, text: str) -> Optional[str]:
        """
        获取情绪分析结果

        调用现有 text_sentiment 模块的 RoBERTa 模型
        返回情绪标签：positive/negative/neutral/anxious/depressed 等
        """
        try:
            # 使用项目现有的文本情绪分析
            from text_sentiment import TextSentimentAnalyzer
            analyzer = TextSentimentAnalyzer()
            result = analyzer.analyze(text)
            return result.get("emotion", "neutral")
        except Exception as e:
            logger.warning(f"情绪分析失败：{e}")
            return None


class ScaleBridge:
    """量表模块桥接"""
    
    @staticmethod
    def get_latest_scores(user_id: int) -> Optional[dict]:
        """
        获取用户最新量表分数

        调用现有 assessment_scales 和数据库模型
        返回：{"PHQ-9": 15, "GAD-7": 10, "created_at": "..."}
        """
        try:
            from models import AssessmentResult
            from sqlalchemy import desc

            # 获取最近的评估记录
            latest = AssessmentResult.query.filter_by(user_id=user_id)\
                .order_by(desc(AssessmentResult.created_at))\
                .first()

            if not latest:
                return None

            result_data = latest.get_results()
            scores = {}

            # 提取 PHQ-9 分数
            if latest.assessment_type == 'single':
                scale_id = result_data.get('scale_id', '')
                if 'PHQ' in scale_id or 'phq' in scale_id:
                    scores['PHQ-9'] = result_data.get('result', {}).get('total_score', 0)
                elif 'GAD' in scale_id or 'gad' in scale_id:
                    scores['GAD-7'] = result_data.get('result', {}).get('total_score', 0)
            elif latest.assessment_type == 'comprehensive':
                for scale_result in result_data.get('results', []):
                    scale_id = scale_result.get('scale_id', '')
                    if 'PHQ' in scale_id or 'phq' in scale_id:
                        scores['PHQ-9'] = scale_result.get('total_score', 0)
                    elif 'GAD' in scale_id or 'gad' in scale_id:
                        scores['GAD-7'] = scale_result.get('total_score', 0)

            return scores if scores else None
        except Exception as e:
            logger.warning(f"获取量表分数失败：{e}")
            return None


class VoiceBridge:
    """语音模块桥接"""
    
    @staticmethod
    def analyze_voice_emotion(audio_path: str) -> Optional[str]:
        """
        分析语音情绪

        调用现有 voice_features 模块
        返回情绪标签：calm/excited/sad/angry/anxious 等
        """
        try:
            from voice_features import VoiceEmotionAnalyzer
            analyzer = VoiceEmotionAnalyzer()
            result = analyzer.analyze(audio_path)
            return result.get("emotion", "neutral")
        except Exception as e:
            logger.warning(f"语音情绪分析失败：{e}")
            return None
    
    @staticmethod
    def is_voice_input(user_input: str) -> bool:
        """判断是否为语音输入（通过文件路径判断）"""
        return user_input.endswith((".wav", ".mp3", ".m4a"))