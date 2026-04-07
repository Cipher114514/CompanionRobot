"""
元气充能陪伴平台 - 统一配置文件
所有开关和配置项都在这里，方便统一管理
"""

import os
from pathlib import Path


# =============================================================================
# 应用基础配置
# =============================================================================

class AppConfig:
    """应用基础配置"""

    # 应用名称和版本
    APP_NAME = "元气充能陪伴平台"
    APP_VERSION = "2.0.0"

    # Flask密钥（生产环境必须修改）
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///mental_health.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 会话配置
    PERMANENT_SESSION_LIFETIME_DAYS = 7


# =============================================================================
# AI模型配置
# =============================================================================

class ModelConfig:
    """AI模型配置"""

    # MindChat 对话模型
    MINDCHAT_MODEL_PATH = os.getenv(
        "MINDCHAT_MODEL_PATH",
        "./models/qwen2-1.5b-instruct/Qwen/qwen2-1___5b-instruct"
    )

    # 是否使用4bit量化（节省显存）
    LOAD_IN_4BIT = os.getenv("LOAD_IN_4BIT", "false").lower() == "true"

    # 文本情绪分析模型
    SENTIMENT_MODEL_PATH = "./models/roberta-base-finetuned-dianping-chinese"

    # 模型加载设备（auto/cpu/cuda）
    MODEL_DEVICE = os.getenv("MODEL_DEVICE", "auto")


# =============================================================================
# 语音功能配置
# =============================================================================

class VoiceConfig:
    """语音功能配置"""

    # ==================== 语音转文字 (ASR) ====================

    # 是否启用语音识别
    ENABLE_ASR = os.getenv("ENABLE_ASR", "true").lower() == "true"

    # Whisper模型大小（tiny/base/small/medium/large）
    WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")

    # ==================== 文字转语音 (TTS) ====================

    # 是否启用语音合成
    ENABLE_TTS = os.getenv("ENABLE_TTS", "true").lower() == "true"

    # TTS语音
    TTS_VOICE = os.getenv("TTS_VOICE", "zh-CN-XiaoxiaoNeural")

    # 音频存储目录
    AUDIO_DIR = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "static", "audio"
    )

    # ==================== 语音情绪识别 ====================

    # 是否启用语音情绪分析（使用轻量级特征模型）
    ENABLE_VOICE_EMOTION = os.getenv("ENABLE_VOICE_EMOTION", "true").lower() == "true"

    # 语音情绪模型（已更新为可用的替代模型）
    # 备选模型（都是基于 Wav2Vec2/XLSR-53，效果与原始模型相当）:
    # - "r-f/wav2vec-english-speech-emotion-recognition" (推荐，2025年最新更新)
    # - "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition" (热门，247k+下载)
    # - "none" (禁用，仅使用文本情绪分析)
    VOICE_EMOTION_MODEL = os.getenv("VOICE_EMOTION_MODEL", "r-f/wav2vec-english-speech-emotion-recognition")

    # 多模态情绪融合权重（优化后：提高语音权重）
    VOICE_EMOTION_WEIGHT = float(os.getenv("VOICE_EMOTION_WEIGHT", "0.30"))
    TEXT_EMOTION_WEIGHT = float(os.getenv("TEXT_EMOTION_WEIGHT", "0.70"))

    # 权重验证（确保总和为1）
    @classmethod
    def validate_weights(cls):
        """验证权重配置"""
        total = cls.VOICE_EMOTION_WEIGHT + cls.TEXT_EMOTION_WEIGHT
        if abs(total - 1.0) > 0.01:
            print(f"[警告] 情绪权重总和不等于1 ({total})，已自动调整")
            cls.VOICE_EMOTION_WEIGHT = 0.25
            cls.TEXT_EMOTION_WEIGHT = 0.75



# =============================================================================
# 年龄适配报告配置
# =============================================================================

class ReportConfig:
    """年龄适配报告配置"""

    # 年龄阈值（基于Piaget认知发展理论）
    MIN_REPORT_AGE_CHILD = int(os.getenv("MIN_REPORT_AGE_CHILD", "10"))
    MIN_REPORT_AGE_TEEN = int(os.getenv("MIN_REPORT_AGE_TEEN", "13"))
    MIN_REPORT_AGE_ADULT = int(os.getenv("MIN_REPORT_AGE_ADULT", "18"))

    # 报告级别定义
    REPORT_LEVELS = {
        "none": {
            "min_age": 0,
            "description": "不展示报告"
        },
        "child": {
            "min_age": MIN_REPORT_AGE_CHILD,
            "description": "儿童简化报告（家长/咨询师参与）"
        },
        "teen": {
            "min_age": MIN_REPORT_AGE_TEEN,
            "description": "青少年适配报告"
        },
        "adult": {
            "min_age": MIN_REPORT_AGE_ADULT,
            "description": "成人完整报告"
        }
    }

    # 模块化报告配置
    ENABLE_MODULAR_REPORT = os.getenv("ENABLE_MODULAR_REPORT", "true").lower() == "true"


# =============================================================================
# 危机检测配置
# =============================================================================

class CrisisConfig:
    """危机检测配置"""

    # 是否启用危机检测
    ENABLE_CRISIS_DETECTION = os.getenv("ENABLE_CRISIS_DETECTION", "true").lower() == "true"

    # 危机关键词列表
    CRISIS_SIGNALS = [
        "绝望", "自杀", "自残", "不想活", "结束生命",
        "death", "suicide", "kill myself", "hopeless"
    ]

    # 危机响应模式
    CRISIS_RESPONSE_MODE = os.getenv("CRISIS_RESPONSE_MODE", "careful")  # careful/immediate

    # 是否记录危机事件
    LOG_CRISIS_EVENTS = os.getenv("LOG_CRISIS_EVENTS", "true").lower() == "true"

    # 危机事件数据库路径
    CRISIS_DB_PATH = os.getenv("CRISIS_DB_PATH", "sqlite:///crisis_events.db")


# =============================================================================
# 多媒体生成配置
# =============================================================================

class MediaConfig:
    """多媒体生成配置"""

    # ==================== 音乐生成 ====================

    # 是否启用音乐生成
    ENABLE_MUSIC_GENERATION = os.getenv("ENABLE_MUSIC_GENERATION", "false").lower() == "true"

    # MusicGen模型
    MUSICGEN_MODEL = os.getenv("MUSICGEN_MODEL", "facebook/musicgen-small")

    # 生成时长（秒）
    MUSIC_DURATION = int(os.getenv("MUSIC_DURATION", "10"))

    # ==================== 视频生成 ====================

    # 是否启用视频生成（预留功能）
    ENABLE_VIDEO_GENERATION = os.getenv("ENABLE_VIDEO_GENERATION", "false").lower() == "true"


# =============================================================================
# 系统提示词配置
# =============================================================================

class PromptConfig:
    """系统提示词配置"""

    # 主系统提示词
    SYSTEM_PROMPT = os.getenv(
        "SYSTEM_PROMPT",
        """你是一位温暖、专业的心理咨询陪伴助手。你的角色是：
1. 提供情感支持和陪伴
2. 倾听用户的困扰和感受
3. 在需要时引导用户寻求专业帮助
4. 不做医学诊断，不提供治疗方案
5. 保持温暖、共情、专业的态度"""
    )

    # 固定系统提示词（用于覆盖AI默认行为）- 优化为中等长度对话
    FIXED_SYSTEM_PROMPT = """你是温暖的陪伴助手。

规则:
1. 回复40字左右，不要超过60字
2. 不要"听起来""听上学"开头
3. 直接对话，适当关心
4. 结合用户之前提到的信息
5. 给予情感支持和实用建议

示例:
- 小明你好，工作辛苦了。压力大时记得深呼吸，给自己一点放松时间。
- 理解你的困扰。试试睡前冥想，帮助大脑放松，改善睡眠质量。
- 明白你的担心。和老板沟通一下，说明你的工作量和困难。"""

    # 对话风格配置
    CONVERSATION_STYLE = os.getenv(
        "CONVERSATION_STYLE",
        "warm"  # warm/professional/friendly
    )

    # 对话长度限制
    MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", "500"))


# =============================================================================
# 性能和资源限制配置
# =============================================================================

class PerformanceConfig:
    """性能和资源配置"""

    # 最大对话历史长度
    MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))

    # 是否启用流式输出
    ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() == "true"

    # 请求超时时间（秒）
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))

    # 最大文件上传大小（MB）
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "16"))

    # 并发处理数
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))


# =============================================================================
# 日志和监控配置
# =============================================================================

class LoggingConfig:
    """日志和监控配置"""

    # 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # 是否启用详细日志
    VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"

    # 日志文件路径
    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "./logs/app.log")

    # 是否启用性能监控
    ENABLE_PERFORMANCE_MONITORING = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"

    # 是否记录对话内容（用于调试和分析）
    LOG_CONVERSATIONS = os.getenv("LOG_CONVERSATIONS", "true").lower() == "true"


# =============================================================================
# 隐私和安全配置
# =============================================================================

class PrivacyConfig:
    """隐私和安全配置"""

    # 是否启用数据加密
    ENABLE_ENCRYPTION = os.getenv("ENABLE_ENCRYPTION", "false").lower() == "true"

    # 数据保留期限（天）
    DATA_RETENTION_DAYS = int(os.getenv("DATA_RETENTION_DAYS", "365"))

    # 是否允许用户导出数据
    ALLOW_DATA_EXPORT = os.getenv("ALLOW_DATA_EXPORT", "true").lower() == "true"

    # 是否允许用户删除数据
    ALLOW_DATA_DELETION = os.getenv("ALLOW_DATA_DELETION", "true").lower() == "true"

    # 隐私政策版本
    PRIVACY_POLICY_VERSION = "1.0"


# =============================================================================
# 功能开关总控
# =============================================================================

class FeatureFlags:
    """功能开关总控 - 快速启用/禁用功能模块"""

    @classmethod
    def get_all_flags(cls):
        """获取所有功能开关状态"""
        return {
            "AI模型": {
                "MindChat对话": True,  # 始终启用
                "4bit量化": ModelConfig.LOAD_IN_4BIT,
                "多设备支持": ModelConfig.MODEL_DEVICE != "cpu"
            },
            "语音功能": {
                "语音识别(ASR)": VoiceConfig.ENABLE_ASR,
                "语音合成(TTS)": VoiceConfig.ENABLE_TTS,
                "语音情绪识别": VoiceConfig.ENABLE_VOICE_EMOTION,
                "多模态情绪融合": VoiceConfig.ENABLE_VOICE_EMOTION
            },
            "用户画像": {
                "用户画像系统": True,
                "信息提取": "名字、年龄、职业、爱好、困扰",
                "提示词集成": "自动融入对话"
            },
            "报告系统": {
                "年龄适配报告": True,  # 始终启用
                "模块化报告": ReportConfig.ENABLE_MODULAR_REPORT,
                "最低年龄": f"{ReportConfig.MIN_REPORT_AGE_CHILD}岁"
            },
            "危机检测": {
                "危机检测": CrisisConfig.ENABLE_CRISIS_DETECTION,
                "危机事件记录": CrisisConfig.LOG_CRISIS_EVENTS
            },
            "多媒体": {
                "音乐生成": MediaConfig.ENABLE_MUSIC_GENERATION,
                "视频生成": MediaConfig.ENABLE_VIDEO_GENERATION
            }
        }

    @classmethod
    def print_status(cls):
        """打印所有功能开关状态"""
        print("\n" + "=" * 60)
        print("元气充能陪伴平台 - 功能开关状态")
        print("=" * 60)

        flags = cls.get_all_flags()

        for category, features in flags.items():
            print(f"\n【{category}】")
            for feature, status in features.items():
                if isinstance(status, bool):
                    status_str = "[已启用]" if status else "[已禁用]"
                elif isinstance(status, str):
                    status_str = status
                else:
                    status_str = str(status)
                print(f"  {feature:<20}: {status_str}")

        print("\n" + "=" * 60)


# =============================================================================
# 配置验证和工具函数
# =============================================================================

def validate_config():
    """验证配置的有效性"""
    errors = []
    warnings = []

    # 验证权重配置
    total_weight = VoiceConfig.VOICE_EMOTION_WEIGHT + VoiceConfig.TEXT_EMOTION_WEIGHT
    if abs(total_weight - 1.0) > 0.01:
        errors.append(f"情绪权重总和不等于1: {total_weight}")

    # 验证年龄配置
    if not (ReportConfig.MIN_REPORT_AGE_CHILD <
            ReportConfig.MIN_REPORT_AGE_TEEN <
            ReportConfig.MIN_REPORT_AGE_ADULT):
        errors.append("年龄阈值配置错误：child < teen < adult")

    # 验证路径配置
    required_dirs = [
        (VoiceConfig.AUDIO_DIR, "音频目录")
    ]

    for dir_path, dir_name in required_dirs:
        if not os.path.exists(dir_path):
            warnings.append(f"{dir_name} 不存在: {dir_path}")

    return errors, warnings


def create_missing_directories():
    """创建不存在的目录"""
    directories = [
        VoiceConfig.AUDIO_DIR,
        LoggingConfig.LOG_FILE_PATH.rsplit('/', 1)[0] if '/' in LoggingConfig.LOG_FILE_PATH else "./logs",
        CrisisConfig.CRISIS_DB_PATH.rsplit('/', 1)[0] if '/' in CrisisConfig.CRISIS_DB_PATH else "./"
    ]

    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"[OK] 创建目录: {dir_path}")


# =============================================================================
# 环境变量快速设置
# =============================================================================

def set_from_env(key, value, value_type="string"):
    """从环境变量设置配置"""
    if value_type == "bool":
        os.environ[key] = "true" if value else "false"
    elif value_type == "int":
        os.environ[key] = str(value)
    elif value_type == "float":
        os.environ[key] = str(value)
    else:
        os.environ[key] = value


# =============================================================================
# 主程序入口（用于测试）
# =============================================================================

if __name__ == "__main__":
    """主程序 - 显示配置状态"""

    # 显示功能开关状态
    FeatureFlags.print_status()

    # 验证配置
    print("\n配置验证:")
    errors, warnings = validate_config()

    if errors:
        print("\n[错误]")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print("\n[警告]")
        for warning in warnings:
            print(f"  - {warning}")

    if not errors and not warnings:
        print("\n[OK] 所有配置正常")

    # 显示环境变量示例
    print("\n" + "=" * 60)
    print("环境变量设置示例")
    print("=" * 60)
    print("""
# 启用/禁用功能
export ENABLE_VOICE_EMOTION=false         # 禁用语音情绪识别
export ENABLE_MODULAR_REPORT=true       # 启用模块化报告

# 模型配置
export MINDCHAT_MODEL_PATH=./models/your_model
export LOAD_IN_4BIT=true                  # 启用4bit量化
    """)

    print("\n" + "=" * 60)
    print("💡 提示：可以通过环境变量或直接修改本文件来调整配置")
    print("=" * 60)
