"""
ASR 语音转文字模块 - 使用 Whisper Small 模型
支持中文语音识别，将语音转换为文字
"""

import whisper
import torch
import os
import subprocess
from typing import Dict, Optional
import warnings
import time

# 抑制 whisper 的警告
warnings.filterwarnings("ignore", category=UserWarning)

# 导入语音特征模块
from voice_features import extract_audio_features


def check_ffmpeg() -> bool:
    """检查 ffmpeg 是否已安装"""
    try:
        subprocess.run(["ffmpeg", "-version"],
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE,
                      timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


class WhisperASR:
    """Whisper 语音识别系统"""

    # 模型大小选项
    MODEL_SIZES = {
        "tiny": 39,      # 最快，准确率 85%
        "base": 74,      # 较快，准确率 90%
        "small": 244,    # 推荐，准确率 95%
        "medium": 769,   # 高准确率 97%
        "large": 1550,   # 最高准确率 98%
    }

    # 常见繁体字映射（部分）
    TRADITIONAL_TO_SIMPLIFIED = {
        # 心理健康相关
        '氣': '气', '壓': '压', '憂': '忧', '鬱': '郁', '療': '疗', '癒': '愈',
        '緒': '绪', '復': '复', '變': '变', '應': '应', '認': '认', '識': '识',
        '驚': '惊', '嚇': '吓', '擔': '担', '恐': '恐', '懼': '惧', '愛': '爱',
        '憐': '怜', '憫': '悯', '樂': '乐', '傷': '伤', '痛': '痛', '苦': '苦',
        '悶': '闷', '煩': '烦', '躁': '躁', '憤': '愤', '怒': '怒', '厭': '厌',
        '倦': '倦', '疲': '疲', '勞': '劳', '累': '累', '沈': '沉', '重': '重',
        '輕': '轻', '鬆': '松', '緊': '紧', '張': '张', '安': '安', '寧': '宁',
        '靜': '静', '穩': '稳', '健': '健', '康': '康', '適': '适', '調': '调',
        '節': '节', '齡': '龄', '臉': '脸', '頻': '频', '腦': '脑', '憶': '忆',

        # 常用字
        '們': '们', '這': '这', '過': '过', '開': '开', '關': '关', '覺': '觉',
        '學': '学', '長': '长', '會': '会', '個': '个', '為': '为', '麼': '么',
        '當': '当', '還': '还', '讓': '让', '經': '经', '點': '点', '線': '线',
        '難': '难', '訊': '讯', '號': '号', '機': '机', '電': '电', '網': '网',
        '頁': '页', '視': '视', '頻': '频', '錯': '错', '誤': '误', '術': '术',
        '標': '标', '題': '题', '響': '响', '現': '现', '實': '实', '際': '际',
        '業': '业', '務': '务', '親': '亲', '媽': '妈', '寶': '宝', '貝': '贝',
        '車': '车', '嚮': '向', '導': '导', '乾': '干', '樣': '样', '種': '种',
        '類': '类', '極': '极', '積': '积', '邊': '边', '對': '对', '時': '时',
        '間': '间', '並': '并', '況': '况', '無': '无', '沒': '没', '習': '习',
        '慣': '惯', '與': '与', '驗': '验', '證': '证', '確': '确', '質': '质',
        '讚': '赞', '嘆': '叹', '興': '兴', '奮': '奋', '從': '从', '來': '来',
        '後': '后', '話': '话', '說': '说', '問': '问', '園': '园', '藝': '艺',
        '專': '专', '豐': '丰', '富': '富',

        # 其他常见字
        '語': '语', '圍': '围', '續': '续', '係': '系',
    }

    def __init__(self, model_size: str = "small", device: Optional[str] = None):
        """
        初始化 Whisper ASR 系统

        Args:
            model_size: 模型大小（tiny/base/small/medium/large）
            device: 设备（cuda/cpu），None 表示自动检测
        """
        self.model_size = model_size
        self.model = None
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        print(f"[ASR] 初始化 Whisper {model_size} 模型...")
        print(f"[ASR] 模型大小: {self.MODEL_SIZES.get(model_size, 'Unknown')} MB")
        print(f"[ASR] 设备: {self.device}")

        # 检查 ffmpeg
        if not check_ffmpeg():
            print(f"[ASR] [WARNING] ffmpeg 未安装！Whisper 需要 ffmpeg 才能处理音频。")
            print(f"[ASR] [INFO] 请安装 ffmpeg: https://ffmpeg.org/download.html")
            print(f"[ASR] [INFO] Windows 用户: 下载 ffmpeg 并添加到系统 PATH")

        try:
            self._load_model()
            print(f"[ASR] [OK] Whisper {model_size} 模型加载成功")
        except Exception as e:
            print(f"[ASR] [ERROR] 模型加载失败: {e}")
            raise

    def _load_model(self):
        """加载 Whisper 模型"""
        try:
            # 尝试加载模型
            self.model = whisper.load_model(
                self.model_size,
                device=self.device
            )
        except Exception as e:
            print(f"[ASR] 首次加载失败，尝试下载模型...")
            print(f"[ASR] 这可能需要几分钟时间（{self.MODEL_SIZES.get(self.model_size, 0)} MB）...")

            # 重新尝试（会自动下载）
            self.model = whisper.load_model(
                self.model_size,
                device=self.device
            )

    def transcribe(
        self,
        audio_path: str,
        language: str = "zh",
        task: str = "transcribe",
        initial_prompt: Optional[str] = None
    ) -> Dict:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            language: 语言代码（zh=中文）
            task: 任务类型（transcribe=转录, translate=翻译）
            initial_prompt: 初始提示（可提高准确率）

        Returns:
            包含转录结果的字典
        """
        # 检查 ffmpeg
        if not check_ffmpeg():
            return {
                "success": False,
                "error": "ffmpeg 未安装。请安装 ffmpeg: https://ffmpeg.org/download.html",
                "text": ""
            }

        # 检查文件是否存在
        if not os.path.exists(audio_path):
            return {
                "success": False,
                "error": f"音频文件不存在: {audio_path}",
                "text": ""
            }

        # 检查文件大小
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            return {
                "success": False,
                "error": "音频文件为空",
                "text": ""
            }

        try:
            print(f"[ASR] 正在转录: {audio_path}")
            print(f"[ASR] 文件大小: {file_size / 1024:.2f} KB")

            # 如果没有提供 initial_prompt，使用简体中文提示
            if initial_prompt is None and language == "zh":
                # 使用简体中文常用字作为初始提示，引导模型输出简体
                initial_prompt = "以下是简体中文对话。你好，我是一个心理助手，请问有什么可以帮你的吗？今天天气真好，心情很愉快，工作压力大，感到焦虑和疲劳。"

            # 转录音频
            result = self.model.transcribe(
                audio_path,
                language=language,
                task=task,
                initial_prompt=initial_prompt,
                fp16=False if self.device == "cpu" else True  # CPU 不使用 fp16
            )

            # 提取结果
            text = result.get("text", "").strip()

            # 繁简转换（如果检测到繁体字）
            if self._contains_traditional_chinese(text):
                print(f"[ASR] 检测到繁体字，转换为简体...")
                text = self._traditional_to_simplified(text)

            segments = result.get("segments", [])
            language_detected = result.get("language", language)

            # 计算时长
            duration = segments[-1]["end"] if segments else 0

            print(f"[ASR] [OK] 转录成功")
            print(f"[ASR]   识别语言: {language_detected}")
            print(f"[ASR]   音频时长: {duration:.2f}秒")
            print(f"[ASR]   识别字数: {len(text)}")

            return {
                "success": True,
                "text": text,
                "language": language_detected,
                "duration": duration,
                "segments": segments,
                "audio_path": audio_path
            }

        except FileNotFoundError as e:
            error_msg = f"找不到音频文件或 ffmpeg: {str(e)}"
            print(f"[ASR] [ERROR] 转录失败: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "text": "",
                "needs_ffmpeg": not check_ffmpeg()
            }

        except Exception as e:
            error_msg = str(e)
            print(f"[ASR] [ERROR] 转录失败: {error_msg}")

            return {
                "success": False,
                "error": error_msg,
                "text": ""
            }

    def _contains_traditional_chinese(self, text: str) -> bool:
        """
        检测文本中是否包含繁体字

        Args:
            text: 要检测的文本

        Returns:
            True 如果包含繁体字
        """
        for char in text:
            if char in self.TRADITIONAL_TO_SIMPLIFIED:
                return True
        return False

    def _traditional_to_simplified(self, text: str) -> str:
        """
        将繁体中文转换为简体中文

        Args:
            text: 繁体中文文本

        Returns:
            简体中文文本
        """
        result = []
        for char in text:
            # 如果是繁体字，转换为简体
            if char in self.TRADITIONAL_TO_SIMPLIFIED:
                result.append(self.TRADITIONAL_TO_SIMPLIFIED[char])
            else:
                result.append(char)
        return ''.join(result)

    def transcribe_with_fallback(
        self,
        audio_path: str,
        language: str = "zh"
    ) -> Dict:
        """
        转录音频（带降级方案）

        如果指定语言失败，尝试自动检测语言

        Args:
            audio_path: 音频文件路径
            language: 首选语言

        Returns:
            转录结果
        """
        # 首次尝试：指定语言
        result = self.transcribe(audio_path, language=language)

        if result["success"]:
            return result

        # 降级方案：自动检测语言
        print(f"[ASR] 指定语言失败，尝试自动检测语言...")
        result = self.transcribe(audio_path, language=None)

        return result


class WhisperASRManager:
    """Whisper ASR 管理器（单例模式）"""

    _instance = None
    _model = None

    def __new__(cls, model_size: str = "small"):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_size: str = "small"):
        """初始化管理器"""
        if not self._initialized:
            self.model_size = model_size
            self._initialized = True

    def get_model(self) -> WhisperASR:
        """获取 ASR 模型（懒加载）"""
        if self._model is None:
            self._model = WhisperASR(model_size=self.model_size)
        return self._model

    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._model is not None

    def transcribe_with_features(self, audio_file_path: str) -> Dict:
        """
        转录音频并提取特征

        参数:
            audio_file_path: 音频文件路径

        返回:
            {
                'text': '转录的文本',
                'audio_features': {...},
                'transcription_time': 1.2,
                'success': True/False,
                'error': None 或错误信息
            }
        """
        start_time = time.time()

        # 1. 转录音频
        model = self.get_model()
        transcribe_result = model.transcribe_with_fallback(audio_file_path, language="zh")

        if not transcribe_result.get("success"):
            return {
                'text': '',
                'audio_features': None,
                'transcription_time': time.time() - start_time,
                'success': False,
                'error': transcribe_result.get('error', '转录失败')
            }

        text = transcribe_result.get('text', '')

        # 2. 提取语音特征
        try:
            audio_features = extract_audio_features(audio_file_path)
            print(f"[ASR] 语音特征提取成功: pitch={audio_features.get('pitch_mean', 0):.2f}Hz, "
                  f"tempo={audio_features.get('tempo', 0):.2f}音节/秒")
        except Exception as e:
            print(f"[ASR] 语音特征提取失败: {e}")
            audio_features = None

        transcription_time = time.time() - start_time

        return {
            'text': text,
            'audio_features': audio_features,
            'transcription_time': transcription_time,
            'success': True,
            'error': None
        }


# 便捷函数
def transcribe_audio(
    audio_path: str,
    model_size: str = "small",
    language: str = "zh"
) -> Dict:
    """
    便捷的音频转录函数

    Args:
        audio_path: 音频文件路径
        model_size: 模型大小
        language: 语言代码

    Returns:
        转录结果
    """
    manager = WhisperASRManager(model_size=model_size)
    asr = manager.get_model()
    return asr.transcribe_with_fallback(audio_path, language=language)


# 测试代码
if __name__ == "__main__":
    import sys

    # 设置 UTF-8 编码
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 60)
    print("测试 Whisper ASR".center(60))
    print("=" * 60)

    # 测试 1: 初始化模型
    print("\n[1] 初始化 Whisper Small 模型...")
    try:
        asr = WhisperASR(model_size="small")
        print("[OK] 模型初始化成功")
    except Exception as e:
        print(f"[FAIL] 模型初始化失败: {e}")
        sys.exit(1)

    # 测试 2: 转录音频（如果有测试音频）
    print("\n[2] 测试音频转录...")
    test_audio = "./casia_samples"

    if os.path.exists(test_audio):
        audio_files = [f for f in os.listdir(test_audio) if f.endswith('.wav')]
        if audio_files:
            audio_path = os.path.join(test_audio, audio_files[0])
            print(f"  使用测试音频: {audio_files[0]}")

            result = asr.transcribe_with_fallback(audio_path)

            if result["success"]:
                print(f"\n[OK] 转录成功")
                print(f"  识别内容: {result['text'][:100]}...")
                print(f"  语言: {result['language']}")
                print(f"  时长: {result['duration']:.2f}秒")
            else:
                print(f"\n[FAIL] 转录失败: {result.get('error', 'Unknown error')}")
        else:
            print("  [INFO] 没有找到测试音频")
    else:
        print("  [INFO] 测试音频目录不存在")

    print("\n" + "=" * 60)
    print("测试完成！".center(60))
    print("=" * 60)
