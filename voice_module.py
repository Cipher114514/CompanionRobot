"""
语音模块 - 为元气充能陪伴平台添加语音交互功能

功能:
1. 语音识别 (ASR): Whisper Tiny - 轻量级中文语音识别
2. 语音合成 (TTS): edge-tts - 高质量中文语音合成
3. 语音情绪分析: 从音频特征提取情绪线索
"""

import os
import sys
import re
import asyncio
import tempfile
from typing import Optional, Dict, Tuple
import torch
import numpy as np
import warnings

warnings.filterwarnings("ignore")


class VoiceASR:
    """语音识别模块 - 基于Whisper Tiny"""

    def __init__(self, model_size: str = "tiny", verbose: bool = True):
        """
        初始化语音识别模块

        Args:
            model_size: 模型大小, 可选 "tiny" (39MB) 或 "base" (74MB)
            verbose: 是否打印信息
        """
        self.model_size = model_size
        self.model = None
        self.device = self._get_device()
        self.verbose = verbose

        if self.verbose:
            print(f"[ASR] 初始化语音识别 (Whisper {model_size})...")

    def _get_device(self) -> str:
        """自动检测运行设备"""
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def load_model(self):
        """加载Whisper模型"""
        try:
            from whisper import load_model
            print(f"   正在加载 Whisper {self.model_size} 模型...")
            print(f"   设备: {self.device}")

            # 加载模型 (中文优化)
            self.model = load_model(self.model_size, device=self.device)

            print(f"   [OK] Whisper {self.model_size} 加载完成!")
            return True

        except ImportError:
            print("   [ERROR] 未安装 whisper 库")
            print("   请运行: pip install openai-whisper")
            return False
        except Exception as e:
            print(f"   [ERROR] 模型加载失败: {e}")
            return False

    def _normalize_punctuation(self, text: str) -> str:
        """
        规范化标点符号 - 修复Whisper识别错误

        核心问题：Whisper把 . 和 : 都念成 ** 或 星号星号

        智能修复策略：
        1. 数字后面 → .
        2. 英文字母后面 → .
        3. 汉字后面 → :
        4. 处理带空格的情况
        """
        if not text:
            return text

        def is_chinese(char):
            """判断是否为中文字符"""
            return '\u4e00' <= char <= '\u9fff'

        def get_char_type(char):
            """获取字符类型"""
            if char.isdigit():
                return 'digit'
            elif char.isalpha() and not is_chinese(char):
                return 'alpha'
            elif is_chinese(char):
                return 'chinese'
            else:
                return 'other'

        def is_punctuation(char):
            """判断是否为标点符号"""
            return char in '.,，。、！？；：""''《》【】（）'

        # ============== 第一步：处理带空格的星号星号 ==============
        def replace_spaced_asterisks(match):
            """处理带空格的星号"""
            prev_char = match.group(1)
            char_type = get_char_type(prev_char)

            if char_type == 'digit':
                return prev_char + '.'
            elif char_type == 'chinese':
                return prev_char + ':'
            else:
                return ''

        text = re.sub(r'(\S)\s+(\*\*|星号星号)\s*', replace_spaced_asterisks, text)

        # 去除标点后多余的空格
        text = re.sub(r'([.:：])\s+(?=[\u4e00-\u9fff0-9A-Za-z])', r'\1', text)

        # ============== 第二步：处理紧连的星号（无空格）=============
        def replace_adjacent_asterisks(match):
            """处理紧连的星号"""
            prev_char = match.group(1)

            if is_punctuation(prev_char):
                return prev_char
            if prev_char.isdigit():
                return prev_char + '.'
            elif prev_char.isalpha() and not is_chinese(prev_char):
                return prev_char + '.'
            else:
                return prev_char + ':'

        text = re.sub(r'([^\s])(\*\*)\s*', replace_adjacent_asterisks, text)
        text = re.sub(r'([^\s])星号星号\s*', replace_adjacent_asterisks, text)

        # ============== 第三步：删除剩余的"星号"文字 ==============
        text = text.replace('星号', '')

        # ============== 第四步：删除剩余的单个星号 ==============
        text = re.sub(r'\*', '', text)

        # ============== 第五步：修复其他标点问题 ==============
        text = text.replace('。。', '。')
        text = text.replace('、。', '，')
        text = re.sub(r'\.{4,}', '…', text)
        text = text.replace('，。', '，')
        text = text.replace('，，', '，')
        text = text.replace('：：', '：')
        text = text.replace('::', ':')
        text = text.replace('？？', '？')
        text = text.replace('！！', '！')
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r' ([，。！？：；、])', r'\1', text)
        text = text.lstrip(' .,，。！？：;；')

        return text.strip()

    def transcribe(
        self,
        audio_path: str,
        language: str = "zh"
    ) -> Optional[str]:
        """
        将语音转录为文本

        Args:
            audio_path: 音频文件路径
            language: 语言代码 (默认 "zh" 中文)

        Returns:
            识别的文本,失败返回 None
        """
        if not self.model:
            if not self.load_model():
                return None

        try:
            # 转录音频
            result = self.model.transcribe(
                audio_path,
                language=language,
                fp16=False  # CPU使用float32
            )

            text = result["text"].strip()

            # 调试：显示原始文本
            if self.verbose:
                print(f"[DEBUG] Whisper原始输出: {text}")

            # 规范化标点符号
            text_normalized = self._normalize_punctuation(text)

            # 调试：显示修复后文本
            if self.verbose:
                print(f"[DEBUG] 标点修复后: {text_normalized}")

            return text_normalized

        except Exception as e:
            print(f"[ERROR] 语音识别失败: {e}")
            return None

    def transcribe_with_details(
        self,
        audio_path: str,
        language: str = "zh"
    ) -> Optional[Dict]:
        """
        转录语音并返回详细信息

        Returns:
            包含文本、置信度等信息的字典
        """
        if not self.model:
            if not self.load_model():
                return None

        try:
            result = self.model.transcribe(
                audio_path,
                language=language,
                fp16=False
            )

            # 提取详细信息
            text = result["text"].strip()

            # 规范化标点符号
            text = self._normalize_punctuation(text)

            segments = result.get("segments", [])

            # 计算平均置信度
            if segments:
                avg_confidence = sum(s.get("avg_logprob", 0) for s in segments) / len(segments)
            else:
                avg_confidence = 0.0

            # 音频时长
            duration = result.get("segments", [{}])[-1].get("end", 0) if segments else 0

            return {
                "text": text,
                "duration": round(duration, 2),
                "confidence": round(avg_confidence, 4),
                "language": language
            }

        except Exception as e:
            print(f"[ERROR] 详细识别失败: {e}")
            return None


class VoiceTTS:
    """语音合成模块 - 基于edge-tts"""

    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural", verbose: bool = True):
        """
        初始化语音合成模块

        Args:
            voice: 语音类型
                - "zh-CN-XiaoxiaoNeural": 女声,温柔 (推荐)
                - "zh-CN-YunyangNeural": 男声,温暖
                - "zh-CN-XiaoyiNeural": 女声,活泼
            verbose: 是否打印信息
        """
        self.voice = voice
        self.temp_dir = tempfile.gettempdir()
        self.verbose = verbose

        if self.verbose:
            print(f"[TTS] 初始化语音合成 (edge-tts)...")
            print(f"   语音: {voice}")

    async def _synthesize_async(self, text: str, output_path: str) -> bool:
        """异步合成语音"""
        try:
            import edge_tts

            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)

            return True

        except ImportError:
            print("[ERROR] 未安装 edge-tts 库")
            print("   请运行: pip install edge-tts")
            return False
        except Exception as e:
            print(f"[ERROR] 语音合成失败: {e}")
            return False

    def synthesize(self, text: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        将文本转换为语音

        Args:
            text: 要合成的文本
            output_path: 输出文件路径 (可选,默认自动生成)

        Returns:
            音频文件路径,失败返回 None
        """
        if not text or not text.strip():
            return None

        # 生成输出路径
        if not output_path:
            import uuid
            filename = f"voice_{uuid.uuid4().hex[:8]}.mp3"
            output_path = os.path.join(self.temp_dir, filename)

        try:
            # 运行异步合成
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            success = loop.run_until_complete(
                self._synthesize_async(text, output_path)
            )
            loop.close()

            if success and os.path.exists(output_path):
                return output_path
            else:
                return None

        except Exception as e:
            print(f"[ERROR] 语音合成异常: {e}")
            return None

    def synthesize_with_emotion(
        self,
        text: str,
        emotion: str = "neutral",
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        根据情绪合成语音

        Args:
            text: 文本内容
            emotion: 情绪类型 ("positive", "negative", "neutral")
            output_path: 输出路径

        Returns:
            音频文件路径
        """
        # 根据情绪选择语音
        emotion_voices = {
            "positive": "zh-CN-XiaoyiNeural",  # 活泼女声
            "negative": "zh-CN-XiaoxiaoNeural",  # 温柔女声
            "neutral": "zh-CN-XiaoxiaoNeural"   # 温柔女声
        }

        self.voice = emotion_voices.get(emotion, "zh-CN-XiaoxiaoNeural")

        return self.synthesize(text, output_path)


class VoiceEmotionAnalyzer:
    """语音情绪分析器 - 从音频特征提取情绪"""

    @staticmethod
    def extract_audio_features(audio_path: str) -> Optional[Dict]:
        """
        提取音频特征用于情绪分析

        Args:
            audio_path: 音频文件路径

        Returns:
            音频特征字典
        """
        try:
            import librosa

            # 加载音频
            y, sr = librosa.load(audio_path, sr=22050)

            features = {}

            # 1. 音频时长
            duration = librosa.get_duration(y=y, sr=sr)
            features["duration"] = round(duration, 2)

            # 2. 平均音量 (RMS energy)
            rms = librosa.feature.rms(y=y)
            features["avg_volume"] = float(np.mean(rms))

            # 3. 语速 (基于零交叉率)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
            features["speech_rate"] = float(np.mean(zero_crossing_rate))

            # 4. 音调变化 (基频)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)

            if pitch_values:
                features["avg_pitch"] = float(np.mean(pitch_values))
                features["pitch_variance"] = float(np.var(pitch_values))
            else:
                features["avg_pitch"] = 0.0
                features["pitch_variance"] = 0.0

            return features

        except ImportError:
            print("[WARNING] 未安装 librosa,跳过音频特征提取")
            print("   可选安装: pip install librosa")
            return None
        except Exception as e:
            print(f"[WARNING] 音频特征提取失败: {e}")
            return None

    @staticmethod
    def analyze_emotion_from_features(features: Dict) -> Dict:
        """
        基于音频特征推断情绪

        Args:
            features: 音频特征字典

        Returns:
            情绪分析结果
        """
        if not features:
            return {"emotion": "unknown", "confidence": 0.0}

        # 简单规则推断 (可替换为机器学习模型)
        emotion_scores = {
            "negative": 0.0,  # 负面情绪得分
            "positive": 0.0   # 正面情绪得分
        }

        # 规则1: 语速快 + 音调不稳定 = 焦虑/负面
        if features.get("speech_rate", 0) > 0.15:
            emotion_scores["negative"] += 0.3

        # 规则2: 音量很小 = 低落/负面
        if features.get("avg_volume", 0) < 0.1:
            emotion_scores["negative"] += 0.2

        # 规则3: 音调变化大 = 情绪波动
        if features.get("pitch_variance", 0) > 1000:
            emotion_scores["negative"] += 0.2

        # 规则4: 适中的音量+语速 = 积极/平静
        if 0.1 < features.get("avg_volume", 0) < 0.3:
            emotion_scores["positive"] += 0.3

        # 判定情绪
        if emotion_scores["negative"] > emotion_scores["positive"]:
            emotion = "negative"
            confidence = min(emotion_scores["negative"], 0.7)
        else:
            emotion = "positive"
            confidence = min(emotion_scores["positive"], 0.7)

        return {
            "emotion": emotion,
            "confidence": round(confidence, 2),
            "audio_features": features
        }


class IntegratedVoiceSystem:
    """整合语音系统"""

    def __init__(
        self,
        asr_model: str = "tiny",
        tts_voice: str = "zh-CN-XiaoxiaoNeural",
        verbose: bool = True
    ):
        """
        初始化整合语音系统

        Args:
            asr_model: ASR模型大小 ("tiny" 或 "base")
            tts_voice: TTS语音类型
            verbose: 是否打印初始化信息
        """
        self.verbose = verbose

        if self.verbose:
            print("\n" + "=" * 60)
            print("初始化语音交互系统".center(60))
            print("=" * 60 + "\n")

        self.asr = VoiceASR(model_size=asr_model, verbose=verbose)
        self.tts = VoiceTTS(voice=tts_voice, verbose=verbose)
        self.emotion_analyzer = VoiceEmotionAnalyzer()

        # 不自动加载ASR模型,延迟加载
        if self.verbose:
            print("\n[OK] 语音系统初始化完成!")
            print("   - 语音识别: Whisper (延迟加载)")
            print("   - 语音合成: edge-tts (就绪)")
            print("   - 音频情绪分析: librosa (可选)")
            print("=" * 60 + "\n")

    def voice_to_text(
        self,
        audio_path: str,
        extract_emotion: bool = True
    ) -> Dict:
        """
        语音转文本 (整合情绪分析)

        Args:
            audio_path: 音频文件路径
            extract_emotion: 是否提取音频情绪

        Returns:
            包含文本、情绪等信息的字典
        """
        # 语音识别
        result = self.asr.transcribe_with_details(audio_path)

        if not result:
            return {
                "success": False,
                "error": "语音识别失败"
            }

        # 可选: 提取音频情绪
        if extract_emotion:
            audio_features = self.emotion_analyzer.extract_audio_features(audio_path)
            if audio_features:
                emotion_result = self.emotion_analyzer.analyze_emotion_from_features(audio_features)
                result["audio_emotion"] = emotion_result
            else:
                result["audio_emotion"] = None

        result["success"] = True
        return result

    def text_to_voice(
        self,
        text: str,
        emotion: str = "neutral"
    ) -> Dict:
        """
        文本转语音

        Args:
            text: 文本内容
            emotion: 情绪类型 (影响语音选择)

        Returns:
            包含音频路径的字典
        """
        if not text or not text.strip():
            return {
                "success": False,
                "error": "文本为空"
            }

        # 合成语音
        audio_path = self.tts.synthesize_with_emotion(text, emotion)

        if audio_path:
            return {
                "success": True,
                "audio_path": audio_path,
                "text": text
            }
        else:
            return {
                "success": False,
                "error": "语音合成失败"
            }


# ==================== 便捷函数 ====================

def create_voice_system(
    asr_model: str = "tiny",
    tts_voice: str = "zh-CN-XiaoxiaoNeural",
    verbose: bool = True
) -> IntegratedVoiceSystem:
    """
    创建语音系统实例

    Args:
        asr_model: ASR模型 ("tiny" 或 "base")
        tts_voice: TTS语音
        verbose: 是否打印初始化信息

    Returns:
        语音系统实例
    """
    return IntegratedVoiceSystem(asr_model=asr_model, tts_voice=tts_voice, verbose=verbose)


if __name__ == "__main__":
    # 测试语音系统
    print("测试语音系统...\n")

    voice_system = create_voice_system()

    # 测试TTS
    print("\n[测试] 语音合成...")
    test_text = "你好,我是你的心理咨询助手。今天感觉怎么样?"
    result = voice_system.text_to_voice(test_text, emotion="positive")

    if result["success"]:
        print(f"[OK] 语音合成成功: {result['audio_path']}")
        print(f"   文本: {result['text']}")
    else:
        print(f"[ERROR] 语音合成失败: {result.get('error')}")

    # 测试ASR (如果有音频文件)
    print("\n[测试] 语音识别...")
    test_audio = "test_audio.wav"  # 需要准备测试音频

    if os.path.exists(test_audio):
        result = voice_system.voice_to_text(test_audio)

        if result["success"]:
            print(f"[OK] 识别成功: {result['text']}")
            print(f"   时长: {result['duration']}s")

            if result.get("audio_emotion"):
                print(f"   音频情绪: {result['audio_emotion']['emotion']}")
        else:
            print(f"[ERROR] 识别失败: {result.get('error')}")
    else:
        print(f"[WARNING] 未找到测试音频: {test_audio}")
