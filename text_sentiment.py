# -*- coding: utf-8 -*-
"""
文本情绪分析器

功能：
1. 基于规则和关键词的中文文本情绪分析
2. 支持正面/负面/中性情绪识别
3. 抑郁风险关键词检测

技术要点：
- 使用情绪词典匹配
- 程度副词和否定词处理
- 句子级别的情绪分析
"""

import re
from typing import Dict


class TextSentimentAnalyzer:
    """文本情绪分析器 - 基于规则和关键词"""

    def __init__(self):
        """初始化文本情绪分析器，构建情绪词典"""
        # 正面情绪词库
        self.positive_words = {
            # 高度正面 (权重 1.0)
            '开心', '快乐', '幸福', '高兴', '愉快', '欣喜', '满足', '舒适',
            '棒', '好', '优秀', '成功', '顺利', '进步', '改善', '提升',
            '喜欢', '爱', '享受', '期待', '希望', '充满', '感谢', '感激',

            # 中度正面 (权重 0.7)
            '不错', '还可以', '挺好', '没事', '放心', '安心', '平静',
            '可以', '能够', '完成', '实现', '达到',

            # 轻微正面 (权重 0.5)
            '还好', '一般', '正常', '平常', '习惯'
        }

        # 负面情绪词库
        self.negative_words = {
            # 高度负面 (权重 1.0)
            '难过', '伤心', '痛苦', '抑郁', '绝望', '崩溃', '窒息',
            '焦虑', '紧张', '恐惧', '害怕', '恐慌', '惊恐', '不安',
            '生气', '愤怒', '烦躁', '恼火', '讨厌', '厌恶', '恨',
            '孤独', '寂寞', '空虚', '无助', '迷茫', '困惑', '失落',
            '疲惫', '累', '疲倦', '精疲力竭', '力不从心',

            # 中度负面 (权重 0.7)
            '不舒服', '难受', '不好', '糟糕', '差', '失败', '问题',
            '担心', '忧虑', '困扰', '麻烦', '困难', '压力',

            # 轻微负面 (权重 0.5)
            '不太', '没', '不', '有点', '一些'
        }

        # 抑郁风险指标词
        self.depression_keywords = {
            # 高风险 (权重 0.8)
            '想死', '自杀', '不想活', '结束', '离开', '消失',
            '绝望', '无意义', '没意义', '没价值', '累赘', '负担',

            # 中风险 (权重 0.6)
            '失眠', '睡不着', '噩梦', '嗜睡', '没胃口', '不想吃',
            '自责', '内疚', '愧疚', '对不起', '抱歉', '没用',

            # 轻微风险 (权重 0.4)
            '累', '疲惫', '无力', '没精神', '没劲', '提不起',
            '孤独', '寂寞', '没人', '空虚', '空白'
        }

        # 否定词（用于反转情绪）
        self.negation_words = {'不', '没', '别', '非', '无', '不是', '没有', '不要'}

        # 程度副词（增强或减弱情绪）
        self.degree_adverbs = {
            '非常': 1.5, '特别': 1.5, '十分': 1.5, '极其': 2.0,
            '很': 1.3, '挺': 1.2, '比较': 1.1, '有点': 0.7,
            '稍微': 0.6, '略微': 0.5, '一点儿': 0.7
        }

    def _analyze_sentence(self, sentence: str) -> Dict:
        """
        分析单个句子的情绪

        返回: {'positive': float, 'negative': float, 'depression_risk': float}
        """
        scores = {'positive': 0.0, 'negative': 0.0, 'depression_risk': 0.0}

        # 检测程度副词
        degree_modifier = 1.0
        for word, modifier in self.degree_adverbs.items():
            if word in sentence:
                degree_modifier = modifier
                break

        # 检测否定词
        has_negation = any(neg in sentence for neg in self.negation_words)

        # 正面词统计
        for word in self.positive_words:
            if word in sentence:
                if has_negation:
                    scores['negative'] += 0.8 * degree_modifier
                else:
                    scores['positive'] += 1.0 * degree_modifier

        # 负面词统计
        for word in self.negative_words:
            if word in sentence:
                if has_negation:
                    scores['positive'] += 0.6 * degree_modifier
                else:
                    scores['negative'] += 1.0 * degree_modifier

        # 抑郁风险词统计
        for word, weight in [('想死', 0.8), ('自杀', 0.8), ('不想活', 0.8),
                            ('绝望', 0.7), ('无意义', 0.7), ('失眠', 0.6),
                            ('孤独', 0.5), ('空虚', 0.5), ('累', 0.4)]:
            if word in sentence:
                scores['depression_risk'] += weight

        return scores

    def analyze(self, text: str) -> Dict:
        """
        分析文本情绪

        参数:
            text: 输入文本

        返回:
            {
                'sentiment': 'positive' | 'negative' | 'neutral',
                'confidence': 0.0-1.0,
                'positive_score': float,
                'negative_score': float,
                'depression_risk': 0.0-1.0
            }
        """
        if not text or not text.strip():
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'positive_score': 0.0,
                'negative_score': 0.0,
                'depression_risk': 0.0
            }

        # 分句
        sentences = re.split(r'[。！？.!?；;]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'positive_score': 0.0,
                'negative_score': 0.0,
                'depression_risk': 0.0
            }

        # 累计分数
        total_positive = 0.0
        total_negative = 0.0
        total_depression = 0.0

        for sentence in sentences:
            scores = self._analyze_sentence(sentence)
            total_positive += scores['positive']
            total_negative += scores['negative']
            total_depression += scores['depression_risk']

        # 归一化分数
        max_score = max(total_positive, total_negative, 1.0)
        positive_score = total_positive / max_score
        negative_score = total_negative / max_score

        # 判定情绪
        if positive_score > negative_score * 1.2:
            sentiment = 'positive'
            confidence = min(positive_score * 0.7, 0.9)
        elif negative_score > positive_score * 1.2:
            sentiment = 'negative'
            confidence = min(negative_score * 0.7, 0.9)
        else:
            sentiment = 'neutral'
            confidence = 0.5

        # 抑郁风险归一化
        depression_risk = min(total_depression / len(sentences), 1.0)

        return {
            'sentiment': sentiment,
            'confidence': round(confidence, 2),
            'positive_score': round(positive_score, 2),
            'negative_score': round(negative_score, 2),
            'depression_risk': round(depression_risk, 2)
        }


# ==================== 便捷函数 ====================

def create_text_analyzer() -> TextSentimentAnalyzer:
    """
    创建文本情绪分析器实例

    返回:
        TextSentimentAnalyzer 实例
    """
    return TextSentimentAnalyzer()


def quick_analyze(text: str) -> Dict:
    """
    快速分析文本情绪（便捷函数）

    参数:
        text: 输入文本

    返回:
        情绪分析结果
    """
    analyzer = create_text_analyzer()
    return analyzer.analyze(text)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("文本情绪分析器 - 测试".center(60))
    print("=" * 60)

    # 创建分析器
    analyzer = create_text_analyzer()

    # 测试案例
    test_texts = [
        "我今天很开心，感觉很好！",
        "我很难过，什么都不想做",
        "我今天感觉一般，没什么特别的",
        "我最近失眠很严重，感觉很绝望",
        "虽然有点累，但整体还不错",
        "不开心，也不想说话"
    ]

    print("\n测试结果：")
    print("-" * 60)

    for text in test_texts:
        result = analyzer.analyze(text)
        print(f"\n文本: {text}")
        print(f"情绪: {result['sentiment']} (置信度: {result['confidence']})")
        print(f"正面得分: {result['positive_score']}, 负面得分: {result['negative_score']}")
        print(f"抑郁风险: {result['depression_risk']}")

    print("\n" + "=" * 60)
    print("测试完成！".center(60))
    print("=" * 60)
