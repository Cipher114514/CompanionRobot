# -*- coding: utf-8 -*-
"""
多模态情绪融合分析器

功能：
1. 融合文本情绪和语音特征进行综合情绪分析
2. 加权融合：文本40% + 语音60%（语音更准确反映真实情绪）
3. 基于语音特征检测抑郁风险

技术要点：
- 使用简单的规则基线（不依赖复杂ML模型）
- 可延迟加载文本分析器
- 详细的情绪分析和风险评估
"""

import re
from typing import Dict, Optional, List, Tuple


class AdaptiveFusionWeights:
    """
    动态权重融合算法

    根据多种因素动态调整文本和语音的融合权重：
    - 音频质量（信噪比、时长）
    - 情绪置信度差异
    - 抑郁风险等级
    """

    def __init__(self):
        """初始化动态权重计算器"""
        # 音频质量阈值
        self.snr_thresholds = {
            'poor': 20,      # < 20dB: 噪音大，降低语音权重
            'fair': 40,      # 20-40dB: 一般
            'good': 40       # > 40dB: 质量好，可以提升语音权重
        }

        # 置信度阈值
        self.confidence_diff_threshold = 0.2  # 置信度差异超过此值时调整权重

        # 抑郁风险阈值（PHQ-9分数）
        self.depression_thresholds = {
            'mild': 10,      # 轻度
            'moderate': 15,  # 中度
            'severe': 20     # 重度
        }

        # 基础权重
        self.base_text_weight = 0.4
        self.base_voice_weight = 0.6

    def calculate_snr(self, audio_path: str) -> Optional[float]:
        """
        计算音频信噪比 (SNR)

        参数:
            audio_path: 音频文件路径

        返回:
            SNR值（dB），如果计算失败返回None
        """
        try:
            import librosa
            import numpy as np

            # 加载音频
            y, sr = librosa.load(audio_path, sr=22050)

            # 计算信号功率
            signal_power = np.mean(y ** 2)

            # 估计噪声功率（使用前0.5秒作为噪声估计）
            noise_samples = int(0.5 * sr)
            if len(y) > noise_samples:
                noise_power = np.mean(y[:noise_samples] ** 2)
            else:
                noise_power = signal_power * 0.01  # 默认噪声水平

            # 避免除零
            if noise_power < 1e-6:
                noise_power = 1e-6

            # 计算SNR (dB)
            snr = 10 * np.log10(signal_power / noise_power)

            return float(snr)

        except Exception as e:
            print(f"[WARNING] SNR计算失败: {e}")
            return None

    def assess_audio_quality(self, audio_features: Dict, audio_path: Optional[str] = None) -> Dict:
        """
        评估音频质量

        参数:
            audio_features: 语音特征字典
            audio_path: 音频文件路径（可选，用于计算SNR）

        返回:
            {
                'quality': 'good' | 'fair' | 'poor',
                'snr': float,
                'duration': float,
                'reasons': List[str]
            }
        """
        quality_factors = []
        snr = None

        # 1. 计算SNR（如果提供了音频路径）
        if audio_path:
            snr = self.calculate_snr(audio_path)
            if snr is not None:
                if snr < self.snr_thresholds['poor']:
                    quality_factors.append('low_snr')
                elif snr > self.snr_thresholds['good']:
                    quality_factors.append('high_snr')

        # 2. 检查时长
        duration = audio_features.get('duration', 0)
        if duration < 1.0:
            quality_factors.append('too_short')
        elif duration > 30.0:
            quality_factors.append('too_long')

        # 3. 判断整体质量
        if 'low_snr' in quality_factors or 'too_short' in quality_factors:
            quality = 'poor'
        elif 'high_snr' in quality_factors and 'too_short' not in quality_factors:
            quality = 'good'
        else:
            quality = 'fair'

        return {
            'quality': quality,
            'snr': snr,
            'duration': duration,
            'factors': quality_factors
        }

    def calculate_weights(self,
                         text_confidence: float,
                         voice_confidence: float,
                         audio_quality: Dict,
                         depression_risk: float = 0.0) -> Tuple[float, float]:
        """
        动态计算融合权重

        参数:
            text_confidence: 文本情绪置信度 (0-1)
            voice_confidence: 语音情绪置信度 (0-1)
            audio_quality: 音频质量评估结果
            depression_risk: 抑郁风险分数 (0-1)

        返回:
            (text_weight, voice_weight): 和为1的权重元组
        """
        text_w = self.base_text_weight
        voice_w = self.base_voice_weight

        # ===== 1. 音频质量调整 =====
        if audio_quality['quality'] == 'poor':
            # 音频质量差：增加文本权重，降低语音权重
            text_w += 0.2
            voice_w -= 0.2
        elif audio_quality['quality'] == 'good':
            # 音频质量好：可以适当增加语音权重
            voice_w += 0.1
            text_w -= 0.1

        # ===== 2. 置信度差异调整 =====
        conf_diff = voice_confidence - text_confidence

        if abs(conf_diff) > self.confidence_diff_threshold:
            # 谁置信度高，给谁更多权重
            adjustment = conf_diff * 0.3  # 调整幅度
            voice_w += adjustment
            text_w -= adjustment

        # ===== 3. 抑郁风险调整 =====
        # 高抑郁风险时，语音更难伪装，增加语音权重
        if depression_risk > 0.6:  # 高风险
            voice_w += 0.15
            text_w -= 0.15
        elif depression_risk > 0.3:  # 中度风险
            voice_w += 0.1
            text_w -= 0.1

        # ===== 4. 归一化确保和为1 =====
        total = text_w + voice_w
        if total > 0:
            text_w = text_w / total
            voice_w = voice_w / total
        else:
            # 如果出现异常，回退到基础权重
            text_w = self.base_text_weight
            voice_w = self.base_voice_weight

        # 限制权重范围在 [0.1, 0.9] 之间，避免极端情况
        text_w = max(0.1, min(0.9, text_w))
        voice_w = 1.0 - text_w

        return round(text_w, 3), round(voice_w, 3)

    def get_weight_explanation(self, text_w: float, voice_w: float,
                                audio_quality: Dict,
                                conf_diff: float,
                                depression_risk: float) -> List[str]:
        """
        生成权重调整的解释说明

        返回: 解释说明列表
        """
        explanations = []

        # 基础权重
        explanations.append(f"基础权重: 文本 {self.base_text_weight*100:.0f}% / 语音 {self.base_voice_weight*100:.0f}%")

        # 音频质量影响
        if audio_quality['quality'] == 'poor':
            explanations.append(f"⚠️ 音频质量较差 ({audio_quality['quality']}), 增加文本权重")
        elif audio_quality['quality'] == 'good':
            explanations.append(f"✓ 音频质量良好 ({audio_quality['quality']}), 适当增加语音权重")

        # 置信度影响
        if abs(conf_diff) > self.confidence_diff_threshold:
            if conf_diff > 0:
                explanations.append(f"📊 语音置信度更高 ({conf_diff:+.2f}), 增加语音权重")
            else:
                explanations.append(f"📊 文本置信度更高 ({conf_diff:+.2f}), 增加文本权重")

        # 抑郁风险影响
        if depression_risk > 0.6:
            explanations.append(f"⚠️ 高抑郁风险 ({depression_risk:.2f}), 语音更难伪装, 增加语音权重")
        elif depression_risk > 0.3:
            explanations.append(f"⚠️ 中度抑郁风险 ({depression_risk:.2f}), 适当增加语音权重")

        # 最终权重
        explanations.append(f"🎯 最终权重: 文本 {text_w*100:.1f}% / 语音 {voice_w*100:.1f}%")

        return explanations


class VoiceBiomarkerAnalyzer:
    """
    语音生物标记分析器（精简版）

    基于学术研究实现的3个核心抑郁生物标记：
    1. 音高变异性 - 抑郁患者语调单调
    2. 停顿模式 - 抑郁患者停顿更频繁、更长
    3. 语速不稳定性 - 抑郁患者语速变化少

    参考文献：
    - Cummins et al. (2015): "Depression and vocal prosody"
    - Oxenberg et al. (2019): "Speech pause patterns in depression"
    - Stasak et al. (2019): "Speech rate variability in depression"
    """

    def __init__(self):
        """初始化生物标记分析器"""
        try:
            import librosa
            import numpy as np
            self.librosa = librosa
            self.np = np
            self.available = True
        except ImportError:
            self.available = False
            print("[WARNING] librosa未安装，生物标记分析器不可用")

    def analyze_pitch_variability(self, pitch_mean: float, pitch_std: float) -> Dict:
        """
        分析音高变异性（单调性）

        学术依据：抑郁患者语调平淡、单调，音高标准差显著降低

        参数:
            pitch_mean: 平均音高
            pitch_std: 音高标准差

        返回:
            {
                'risk_score': 0.0-1.0,
                'interpretation': str,
                'monotonicity_level': 'high' | 'medium' | 'low'
            }
        """
        if not self.available:
            return {'risk_score': 0.0, 'interpretation': '分析器不可用'}

        # 音高变异性的风险阈值（基于研究文献）
        # 正常人: pitch_std > 50Hz
        # 轻度抑郁: 30-50Hz
        # 重度抑郁: < 30Hz

        if pitch_std < 30:
            risk_score = 0.85
            monotonicity = 'high'
            interpretation = '语调高度单调，音高变化极少，强烈提示抑郁症状'
        elif pitch_std < 50:
            risk_score = 0.55
            monotonicity = 'medium'
            interpretation = '语调偏单调，音高变化较少，可能存在抑郁倾向'
        else:
            risk_score = 0.15
            monotonicity = 'low'
            interpretation = '语调丰富自然，音高变化正常'

        return {
            'risk_score': round(risk_score, 2),
            'pitch_std': round(pitch_std, 2),
            'monotonicity_level': monotonicity,
            'interpretation': interpretation
        }

    def analyze_pause_pattern(self, audio_path: str) -> Dict:
        """
        分析停顿模式

        学术依据：抑郁患者思维迟缓，导致语音中停顿更频繁、持续时间更长

        参数:
            audio_path: 音频文件路径

        返回:
            {
                'pause_count': int,
                'avg_pause_duration': float,
                'total_pause_ratio': float,
                'risk_score': 0.0-1.0
            }
        """
        if not self.available:
            return {'risk_score': 0.0, 'interpretation': '分析器不可用'}

        try:
            # 加载音频
            y, sr = self.librosa.load(audio_path, sr=22050)

            # 使用librosa分割音频（检测静音段）
            # top_db=30: 低于峰值30dB视为静音
            intervals = self.librosa.effects.split(y, top_db=30)

            if len(intervals) < 2:
                # 没有停顿
                return {
                    'pause_count': 0,
                    'avg_pause_duration': 0.0,
                    'total_pause_ratio': 0.0,
                    'risk_score': 0.0,
                    'interpretation': '无明显停顿模式'
                }

            # 计算停顿
            pauses = []
            for i in range(len(intervals) - 1):
                # 当前段结束到下一段开始的时间差
                pause_start = intervals[i][1]
                pause_end = intervals[i + 1][0]
                pause_duration = (pause_end - pause_start) / sr  # 转换为秒
                if pause_duration > 0.1:  # 忽略微小停顿
                    pauses.append(pause_duration)

            if not pauses:
                return {
                    'pause_count': 0,
                    'avg_pause_duration': 0.0,
                    'total_pause_ratio': 0.0,
                    'risk_score': 0.0,
                    'interpretation': '无明显停顿'
                }

            pause_count = len(pauses)
            avg_pause_duration = self.np.mean(pauses)
            total_pause_time = self.np.sum(pauses)
            total_duration = len(y) / sr
            total_pause_ratio = total_pause_time / total_duration

            # 风险评估（基于文献数据）
            # 正常: 停顿占比 < 15%
            # 轻度: 15-25%
            # 重度: > 25%

            if total_pause_ratio > 0.25 or avg_pause_duration > 1.0:
                risk_score = 0.80
                severity = '高'
                interpretation = f'停顿模式异常：共{pause_count}次停顿，平均{avg_pause_duration:.2f}秒，停顿占比{total_pause_ratio*100:.1f}%，提示思维迟缓'
            elif total_pause_ratio > 0.15 or avg_pause_duration > 0.6:
                risk_score = 0.50
                severity = '中'
                interpretation = f'停顿模式偏多：共{pause_count}次停顿，平均{avg_pause_duration:.2f}秒，停顿占比{total_pause_ratio*100:.1f}%，可能存在思维迟缓'
            else:
                risk_score = 0.10
                severity = '低'
                interpretation = f'停顿模式正常：共{pause_count}次停顿，平均{avg_pause_duration:.2f}秒'

            return {
                'pause_count': pause_count,
                'avg_pause_duration': round(avg_pause_duration, 2),
                'total_pause_ratio': round(total_pause_ratio, 3),
                'risk_score': round(risk_score, 2),
                'severity': severity,
                'interpretation': interpretation
            }

        except Exception as e:
            print(f"[ERROR] 停顿模式分析失败: {e}")
            return {'risk_score': 0.0, 'interpretation': f'分析失败: {str(e)}'}

    def analyze_speech_instability(self, tempo: float, audio_path: str = None,
                                   tempo_segments: list = None) -> Dict:
        """
        分析语速不稳定性

        学术依据：抑郁患者语速缺乏变化，过于稳定（缺乏抑扬顿挫的情感表达）

        参数:
            tempo: 平均语速
            audio_path: 音频文件路径（可选，用于分段分析）
            tempo_segments: 语速分段列表（可选，如果已预先计算）

        返回:
            {
                'tempo_mean': float,
                'tempo_std': float,
                'tempo_cv': float,  # 变异系数
                'risk_score': 0.0-1.0
            }
        """
        if not self.available:
            return {'risk_score': 0.0, 'interpretation': '分析器不可用'}

        # 如果提供了分段语速，使用它
        if tempo_segments:
            tempo_values = tempo_segments
        else:
            # 否则，假设语速相对稳定（无分段数据）
            # 使用单一值，变异为0
            tempo_values = [tempo]

        tempo_mean = self.np.mean(tempo_values)
        tempo_std = self.np.std(tempo_values)
        tempo_cv = tempo_std / (tempo_mean + 1e-6)  # 变异系数

        # 风险评估
        # 正常: CV > 0.2 (语速有变化)
        # 轻度: 0.1-0.2
        # 重度: < 0.1 (语速过于稳定)

        if tempo_cv < 0.1:
            risk_score = 0.70
            stability = '高'
            interpretation = f'语速过于稳定（变异系数{tempo_cv:.3f}），缺乏情感表达的抑扬顿挫，提示情感平淡'
        elif tempo_cv < 0.2:
            risk_score = 0.40
            stability = '中'
            interpretation = f'语速变化偏少（变异系数{tempo_cv:.3f}），情感表达不够丰富'
        else:
            risk_score = 0.10
            stability = '正常'
            interpretation = f'语速变化正常（变异系数{tempo_cv:.3f}），有自然的抑扬顿挫'

        return {
            'tempo_mean': round(tempo_mean, 2),
            'tempo_std': round(tempo_std, 2),
            'tempo_cv': round(tempo_cv, 3),
            'stability_level': stability,
            'risk_score': round(risk_score, 2),
            'interpretation': interpretation
        }

    def analyze_biomarkers(self, audio_path: str, audio_features: Dict) -> Dict:
        """
        综合分析所有生物标记

        参数:
            audio_path: 音频文件路径
            audio_features: 已提取的基础特征

        返回:
            {
                'overall_risk_score': 0.0-1.0,
                'pitch_analysis': {...},
                'pause_analysis': {...},
                'tempo_analysis': {...},
                'summary': str
            }
        """
        if not self.available:
            return {
                'overall_risk_score': 0.0,
                'summary': '生物标记分析器不可用'
            }

        # 1. 音高变异性分析
        pitch_analysis = self.analyze_pitch_variability(
            audio_features.get('pitch_mean', 150),
            audio_features.get('pitch_std', 50)
        )

        # 2. 停顿模式分析
        pause_analysis = self.analyze_pause_pattern(audio_path)

        # 3. 语速不稳定性分析
        tempo_analysis = self.analyze_speech_instability(
            audio_features.get('tempo', 3.0),
            audio_path
        )

        # 综合风险评分（加权平均）
        # 权重基于学术文献中各指标的相关性
        weights = {
            'pitch': 0.35,   # 音高单调性
            'pause': 0.40,   # 停顿模式（最强指标）
            'tempo': 0.25    # 语速不稳定性
        }

        overall_risk = (
            pitch_analysis['risk_score'] * weights['pitch'] +
            pause_analysis['risk_score'] * weights['pause'] +
            tempo_analysis['risk_score'] * weights['tempo']
        )

        # 生成总结
        high_risk_markers = []
        if pitch_analysis['risk_score'] > 0.6:
            high_risk_markers.append("语调单调")
        if pause_analysis['risk_score'] > 0.6:
            high_risk_markers.append("停顿频繁")
        if tempo_analysis['risk_score'] > 0.6:
            high_risk_markers.append("语速缺乏变化")

        if overall_risk > 0.7:
            summary = f"高风险：检测到多个抑郁相关语音标记（{', '.join(high_risk_markers)}），建议重点关注"
        elif overall_risk > 0.4:
            summary = f"中等风险：存在部分抑郁相关语音标记（{', '.join(high_risk_markers) if high_risk_markers else '轻微异常'}），建议关注"
        else:
            summary = "低风险：语音生物标记正常，未检测到明显抑郁迹象"

        return {
            'overall_risk_score': round(overall_risk, 2),
            'risk_level': '高' if overall_risk > 0.7 else '中' if overall_risk > 0.4 else '低',
            'pitch_analysis': pitch_analysis,
            'pause_analysis': pause_analysis,
            'tempo_analysis': tempo_analysis,
            'summary': summary
        }


class VoiceFeatureExtractor:
    """语音特征提取器 - 从现有语音模块提取特征"""

    def __init__(self):
        """初始化语音特征提取器"""
        try:
            import librosa
            self.librosa_available = True
        except ImportError:
            self.librosa_available = False
            print("[WARNING] 未安装 librosa，语音特征提取将受限")
            print("   可选安装: pip install librosa")

    def extract_features(self, audio_path: str) -> Optional[Dict]:
        """
        提取音频特征

        参数:
            audio_path: 音频文件路径

        返回:
            包含以下特征的字典：
            {
                'pitch_mean': 平均音高 (Hz)
                'pitch_std': 音高标准差
                'energy': 平均能量
                'tempo': 语速 (音节/秒)
                'shimmer': 颤音幅度
                'duration': 音频时长
            }
        """
        if not self.librosa_available:
            return None

        try:
            import librosa
            import numpy as np

            # 加载音频
            y, sr = librosa.load(audio_path, sr=22050)

            features = {}

            # 1. 音频时长
            duration = librosa.get_duration(y=y, sr=sr)
            features['duration'] = round(duration, 2)

            # 2. 平均能量 (RMS)
            rms = librosa.feature.rms(y=y)
            features['energy'] = float(np.mean(rms))

            # 3. 音高特征 (基频)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []

            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)

            if pitch_values:
                features['pitch_mean'] = float(np.mean(pitch_values))
                features['pitch_std'] = float(np.std(pitch_values))
            else:
                features['pitch_mean'] = 0.0
                features['pitch_std'] = 0.0

            # 4. 语速 (基于零交叉率)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
            features['tempo'] = float(np.mean(zero_crossing_rate) * 10)  # 缩放以获得更合理的范围

            # 5. 颤音 (shimmer - 幅度变化)
            if len(pitch_values) > 1:
                # 简化版颤音计算：相邻音高差异
                diffs = np.abs(np.diff(pitch_values))
                features['shimmer'] = float(np.mean(diffs) / (np.mean(pitch_values) + 1e-6))
            else:
                features['shimmer'] = 0.0

            return features

        except Exception as e:
            print(f"[ERROR] 音频特征提取失败: {e}")
            return None


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
            '可以', '能够', '成功', '完成', '实现', '达到',

            # 轻微正面 (权重 0.5)
            '还好', '一般', '正常', '平常', '习惯'
        }

        # 负面情绪词库
        self.negative_words = {
            # 高度负面 (权重 1.0)
            '难过', '伤心', '痛苦', '痛苦', '抑郁', '绝望', '崩溃', '窒息',
            '焦虑', '紧张', '恐惧', '害怕', '恐慌', '惊恐', '不安',
            '生气', '愤怒', '烦躁', '恼火', '讨厌', '厌恶', '恨',
            '孤独', '寂寞', '空虚', '无助', '迷茫', '困惑', '失落',
            '疲惫', '累', '疲倦', '精疲力竭', '力不从心',

            # 中度负面 (权重 0.7)
            '不舒服', '难受', '不好', '糟糕', '差', '失败', '问题',
            '担心', '忧虑', '困扰', '麻烦', '困难', '压力',

            # 轻微负面 (权重 0.5)
            '不太', '没', '不', '有点', '一些', '困扰'
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


class MultimodalSentimentAnalyzer:
    """多模态情绪融合分析器"""

    def __init__(self, use_adaptive_weights: bool = True, use_biomarkers: bool = True):
        """
        初始化多模态情绪分析器

        参数:
            use_adaptive_weights: 是否使用动态权重融合（默认True）
            use_biomarkers: 是否启用语音生物标记分析（默认True）
        """
        self.text_analyzer = None  # 延迟加载
        self.voice_analyzer = VoiceFeatureExtractor()

        # 融合权重（基础权重，会被动态权重覆盖）
        self.text_weight = 0.4   # 文本权重 40%
        self.voice_weight = 0.6  # 语音权重 60%（更准确）

        # 动态权重计算器
        self.use_adaptive_weights = use_adaptive_weights
        if use_adaptive_weights:
            self.weight_calculator = AdaptiveFusionWeights()
            print("[OK] 动态权重融合算法已启用")
        else:
            self.weight_calculator = None
            print("[INFO] 使用固定权重融合: 文本40% / 语音60%")

        # 生物标记分析器
        self.use_biomarkers = use_biomarkers
        if use_biomarkers:
            self.biomarker_analyzer = VoiceBiomarkerAnalyzer()
            if self.biomarker_analyzer.available:
                print("[OK] 语音生物标记分析器已启用")
            else:
                print("[WARNING] 语音生物标记分析器初始化失败，将使用基础特征")
                self.biomarker_analyzer = None
        else:
            self.biomarker_analyzer = None

    def _get_text_analyzer(self):
        """延迟加载文本分析器"""
        if self.text_analyzer is None:
            self.text_analyzer = TextSentimentAnalyzer()
        return self.text_analyzer

    def analyze_text_only(self, text: str) -> Dict:
        """
        仅分析文本情绪

        参数:
            text: 用户输入的文本

        返回:
            {
                'sentiment': 'positive' | 'negative' | 'neutral',
                'confidence': 0.0-1.0,
                'positive_score': float,
                'negative_score': float,
                'depression_risk': 0.0-1.0
            }
        """
        analyzer = self._get_text_analyzer()
        return analyzer.analyze(text)

    def analyze_voice_only(self, audio_features: Dict) -> Dict:
        """
        仅分析语音情绪

        参数:
            audio_features: 语音特征字典

        返回:
            {
                'sentiment': 'positive' | 'negative' | 'neutral',
                'confidence': 0.0-1.0,
                'risk_indicators': {...}
            }
        """
        if not audio_features:
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'risk_indicators': {}
            }

        # 基于语音特征的情绪评分
        negative_score = 0.0
        positive_score = 0.0
        risk_indicators = {}

        # 规则1: 低音高 -> 负面情绪（抑郁倾向）
        if audio_features.get('pitch_mean', 200) < 150:
            negative_score += 0.3
            risk_indicators['low_pitch'] = True
        else:
            risk_indicators['low_pitch'] = False

        # 规则2: 快语速 -> 焦虑/紧张
        if audio_features.get('tempo', 3.0) > 4.0:
            negative_score += 0.2
            risk_indicators['fast_tempo'] = True
        else:
            risk_indicators['fast_tempo'] = False

        # 规则3: 低能量 -> 低落/疲惫
        if audio_features.get('energy', 0.05) < 0.02:
            negative_score += 0.2
            risk_indicators['low_energy'] = True
        else:
            risk_indicators['low_energy'] = False

        # 规则4: 高颤音 -> 情绪不稳定
        if audio_features.get('shimmer', 0.05) > 0.1:
            negative_score += 0.3
            risk_indicators['high_shimmer'] = True
        else:
            risk_indicators['high_shimmer'] = False

        # 规则5: 适中的音量和语速 -> 积极/平静
        if (0.02 < audio_features.get('energy', 0.05) < 0.1 and
            2.0 < audio_features.get('tempo', 3.0) < 4.0):
            positive_score += 0.3

        # 判定情绪
        if negative_score > positive_score:
            sentiment = 'negative'
            confidence = min(negative_score * 0.8, 0.95)
        elif positive_score > negative_score:
            sentiment = 'positive'
            confidence = min(positive_score * 0.8, 0.85)
        else:
            sentiment = 'neutral'
            confidence = 0.5

        return {
            'sentiment': sentiment,
            'confidence': round(confidence, 2),
            'negative_score': round(negative_score, 2),
            'positive_score': round(positive_score, 2),
            'risk_indicators': risk_indicators
        }

    def analyze_multimodal(self, text: str, audio_features: Optional[Dict] = None,
                          audio_path: Optional[str] = None) -> Dict:
        """
        融合分析文本和语音情绪

        参数:
            text: 用户输入的文本
            audio_features: dict, 已提取的语音特征字典（可选）
            audio_path: str, 音频文件路径（可选，如果没有提供audio_features）

        返回:
            {
                'overall_sentiment': 'negative',
                'confidence': 0.89,
                'text_contribution': 0.75,  # 文本分析得分
                'voice_contribution': 0.92, # 语音分析得分
                'fusion_details': {
                    'text_sentiment': 'negative',
                    'text_confidence': 0.75,
                    'voice_sentiment': 'negative',
                    'voice_confidence': 0.92
                },
                'risk_indicators': {
                    'low_pitch': True,
                    'fast_tempo': False,
                    'low_energy': True,
                    'high_shimmer': True
                },
                'depression_risk': 0.75  # 抑郁风险分数
            }
        """
        # 分析文本情绪
        text_result = self.analyze_text_only(text)
        text_sentiment = text_result['sentiment']
        text_confidence = text_result['confidence']

        # 如果没有提供音频特征，尝试从音频文件提取
        if audio_features is None and audio_path:
            audio_features = self.voice_analyzer.extract_features(audio_path)

        # 分析语音情绪
        if audio_features:
            voice_result = self.analyze_voice_only(audio_features)
            voice_sentiment = voice_result['sentiment']
            voice_confidence = voice_result['confidence']
            risk_indicators = voice_result['risk_indicators']

            # 检测抑郁风险
            depression_risk = self.detect_depression_risk(audio_features)
        else:
            # 没有音频特征，仅使用文本分析
            voice_sentiment = 'neutral'
            voice_confidence = 0.0
            risk_indicators = {}
            depression_risk = text_result.get('depression_risk', 0.0)

        # ===== 动态权重计算 =====
        if self.use_adaptive_weights and audio_features:
            # 评估音频质量
            audio_quality = self.weight_calculator.assess_audio_quality(
                audio_features,
                audio_path
            )

            # 计算动态权重
            text_weight, voice_weight = self.weight_calculator.calculate_weights(
                text_confidence=text_confidence,
                voice_confidence=voice_confidence,
                audio_quality=audio_quality,
                depression_risk=depression_risk
            )

            # 生成权重解释
            conf_diff = voice_confidence - text_confidence
            weight_explanation = self.weight_calculator.get_weight_explanation(
                text_weight, voice_weight, audio_quality, conf_diff, depression_risk
            )
        else:
            # 使用固定权重
            text_weight = self.text_weight
            voice_weight = self.voice_weight
            audio_quality = {}
            weight_explanation = [
                f"使用固定权重: 文本 {text_weight*100:.0f}% / 语音 {voice_weight*100:.0f}%"
            ]

        # 融合决策
        # 将情绪转换为数值：positive=1, neutral=0, negative=-1
        sentiment_values = {'positive': 1, 'neutral': 0, 'negative': -1}

        # 计算加权得分
        text_score = sentiment_values[text_sentiment] * text_confidence
        voice_score = sentiment_values[voice_sentiment] * voice_confidence

        # 融合分数（加权平均）
        if voice_confidence > 0.1:  # 有有效的语音分析
            fused_score = (text_score * text_weight +
                          voice_score * voice_weight)
            overall_confidence = (text_confidence * text_weight +
                                 voice_confidence * voice_weight)
        else:  # 仅文本分析
            fused_score = text_score
            overall_confidence = text_confidence
            text_weight = 1.0
            voice_weight = 0.0

        # 判定最终情绪
        if fused_score > 0.3:
            overall_sentiment = 'positive'
        elif fused_score < -0.3:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'

        # ===== 生物标记分析（可选）=====
        biomarker_analysis = None
        if self.biomarker_analyzer and audio_features and audio_path:
            try:
                biomarker_analysis = self.biomarker_analyzer.analyze_biomarkers(
                    audio_path=audio_path,
                    audio_features=audio_features
                )
                # 生物标记的风险评分可以与传统特征结合
                if biomarker_analysis.get('overall_risk_score'):
                    # 结合生物标记调整抑郁风险（权重0.7传统 + 0.3生物标记）
                    depression_risk = (
                        depression_risk * 0.7 +
                        biomarker_analysis['overall_risk_score'] * 0.3
                    )
            except Exception as e:
                print(f"[WARNING] 生物标记分析失败: {e}")
                biomarker_analysis = None

        return {
            'overall_sentiment': overall_sentiment,
            'confidence': round(min(overall_confidence, 0.95), 2),
            'text_contribution': round(text_confidence, 2),
            'voice_contribution': round(voice_confidence, 2),
            'fusion_details': {
                'text_sentiment': text_sentiment,
                'text_confidence': text_confidence,
                'voice_sentiment': voice_sentiment,
                'voice_confidence': voice_confidence,
                'text_score': round(text_score, 2),
                'voice_score': round(voice_score, 2),
                'fused_score': round(fused_score, 2),
                'text_weight': text_weight,
                'voice_weight': voice_weight,
                'weight_explanation': weight_explanation
            },
            'audio_quality': audio_quality if audio_quality else None,
            'risk_indicators': risk_indicators,
            'depression_risk': round(depression_risk, 2),
            'biomarker_analysis': biomarker_analysis  # 新增：生物标记分析结果
        }

    @property
    def weight(self):
        """获取语音权重"""
        return self.voice_weight

    def detect_depression_risk(self, features: Dict) -> float:
        """
        基于语音特征检测抑郁风险

        规则：
        - 低音高（pitch_mean < 150）: +0.3
        - 快语速（tempo > 4.0）: +0.2
        - 低能量（energy < 0.02）: +0.2
        - 高颤音（shimmer > 0.1）: +0.3

        参数:
            features: 语音特征字典

        返回: 0-1之间的风险分数
        """
        if not features:
            return 0.0

        risk_score = 0.0

        # 规则1: 低音高
        if features.get('pitch_mean', 200) < 150:
            risk_score += 0.3

        # 规则2: 快语速（焦虑）
        if features.get('tempo', 3.0) > 4.0:
            risk_score += 0.2

        # 规则3: 低能量（低落）
        if features.get('energy', 0.05) < 0.02:
            risk_score += 0.2

        # 规则4: 高颤音（情绪不稳定）
        if features.get('shimmer', 0.05) > 0.1:
            risk_score += 0.3

        # 归一化到 0-1 范围
        return min(risk_score, 1.0)


# ==================== 便捷函数 ====================

def create_multimodal_analyzer(use_adaptive_weights: bool = True,
                               use_biomarkers: bool = True) -> MultimodalSentimentAnalyzer:
    """
    创建多模态情绪分析器实例

    参数:
        use_adaptive_weights: 是否使用动态权重融合（默认True）
        use_biomarkers: 是否启用语音生物标记分析（默认True）

    返回:
        MultimodalSentimentAnalyzer 实例
    """
    return MultimodalSentimentAnalyzer(
        use_adaptive_weights=use_adaptive_weights,
        use_biomarkers=use_biomarkers
    )


def quick_analyze(text: str, audio_path: str = None) -> Dict:
    """
    快速分析情绪（便捷函数）

    参数:
        text: 输入文本
        audio_path: 音频文件路径（可选）

    返回:
        融合分析结果
    """
    analyzer = create_multimodal_analyzer()
    return analyzer.analyze_multimodal(text, audio_path=audio_path)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("多模态情绪融合分析器 - 测试".center(60))
    print("=" * 60)

    # 创建分析器
    analyzer = create_multimodal_analyzer()

    # 测试1: 仅文本分析
    print("\n[测试1] 仅文本情绪分析")
    print("-" * 60)

    test_texts = [
        "我今天很开心，感觉很好！",
        "我很难过，什么都不想做",
        "我今天感觉一般，没什么特别的",
        "我最近失眠很严重，感觉很绝望"
    ]

    for text in test_texts:
        result = analyzer.analyze_text_only(text)
        print(f"\n文本: {text}")
        print(f"情绪: {result['sentiment']} (置信度: {result['confidence']})")
        print(f"正面得分: {result['positive_score']}, 负面得分: {result['negative_score']}")
        print(f"抑郁风险: {result['depression_risk']}")

    # 测试2: 仅语音分析（模拟特征）
    print("\n\n[测试2] 仅语音情绪分析")
    print("-" * 60)

    # 模拟不同的语音特征
    mock_audio_features = [
        {
            'pitch_mean': 180,  # 正常音高
            'energy': 0.05,     # 正常能量
            'tempo': 3.5,       # 正常语速
            'shimmer': 0.06     # 正常颤音
        },
        {
            'pitch_mean': 120,  # 低音高
            'energy': 0.015,    # 低能量
            'tempo': 2.5,       # 慢语速
            'shimmer': 0.12     # 高颤音
        }
    ]

    for i, features in enumerate(mock_audio_features, 1):
        result = analyzer.analyze_voice_only(features)
        print(f"\n测试场景 {i}:")
        print(f"语音特征: {features}")
        print(f"情绪: {result['sentiment']} (置信度: {result['confidence']})")
        print(f"风险指标: {result['risk_indicators']}")

    # 测试3: 多模态融合
    print("\n\n[测试3] 多模态融合分析")
    print("-" * 60)

    test_cases = [
        {
            'text': "我今天感觉不太好",
            'features': {
                'pitch_mean': 130,
                'energy': 0.018,
                'tempo': 2.8,
                'shimmer': 0.11
            }
        },
        {
            'text': "我今天很开心！",
            'features': {
                'pitch_mean': 200,
                'energy': 0.06,
                'tempo': 3.8,
                'shimmer': 0.05
            }
        }
    ]

    for i, case in enumerate(test_cases, 1):
        result = analyzer.analyze_multimodal(
            case['text'],
            audio_features=case['features']
        )

        print(f"\n测试场景 {i}:")
        print(f"文本: {case['text']}")
        print(f"语音特征: {case['features']}")
        print(f"\n融合结果:")
        print(f"  整体情绪: {result['overall_sentiment']}")
        print(f"  置信度: {result['confidence']}")
        print(f"  文本贡献: {result['text_contribution']}")
        print(f"  语音贡献: {result['voice_contribution']}")
        print(f"  抑郁风险: {result['depression_risk']}")
        print(f"  风险指标: {result['risk_indicators']}")
        print(f"  融合详情: {result['fusion_details']}")

    # 测试4: 抑郁风险检测
    print("\n\n[测试4] 抑郁风险检测")
    print("-" * 60)

    risk_test_cases = [
        {'pitch_mean': 140, 'energy': 0.015, 'tempo': 4.5, 'shimmer': 0.12},  # 高风险
        {'pitch_mean': 180, 'energy': 0.05, 'tempo': 3.5, 'shimmer': 0.06},   # 低风险
        {'pitch_mean': 130, 'energy': 0.018, 'tempo': 3.0, 'shimmer': 0.08}   # 中等风险
    ]

    for i, features in enumerate(risk_test_cases, 1):
        risk = analyzer.detect_depression_risk(features)
        print(f"\n测试 {i}: {features}")
        print(f"抑郁风险分数: {risk:.2f}")

    print("\n" + "=" * 60)
    print("测试完成！".center(60))
    print("=" * 60)
