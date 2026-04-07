"""危机检测模块配置"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class CrisisConfig:
    """配置项"""
    
    # 检测开关
    ENABLE_TEXT_DETECTION: bool = True
    ENABLE_VOICE_DETECTION: bool = True
    ENABLE_SCALE_DETECTION: bool = True
    
    # 分级阈值（置信度）
    # 注意：单个关键词的得分：low=0.15, medium=0.25, high=0.4
    # 阈值应该确保单个关键词也能触发相应等级
    LEVEL_1_THRESHOLD: float = 0.1   # 降低阈值，确保单个低危关键词(0.15)也能触发
    LEVEL_2_THRESHOLD: float = 0.2   # 降低阈值，确保单个中危关键词(0.25)也能触发
    LEVEL_3_THRESHOLD: float = 0.35  # 降低阈值，确保单个高危关键词(0.4)也能触发
    
    # 量表预警分数（PHQ-9 总分 0-27）
    PHQ9_WARNING_SCORE: int = 10
    PHQ9_CRITICAL_SCORE: int = 20
    
    # AI 生成配置
    USE_AI_GENERATION: bool = True
    AI_GENERATOR_TIMEOUT: int = 5
    
    # 资源配置
    ENABLE_RESOURCES: bool = False
    RESOURCES_FILE: Optional[Path] = None
    
    # 日志配置
    ENABLE_AUTO_LOG: bool = True
    LOG_FILE_PATH: str = "logs/crisis.log"
    
    # 数据文件路径
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).parent / "data")
    KEYWORDS_FILE: Optional[Path] = None
    RESPONSES_FILE: Optional[Path] = None
    
    # 缓存配置
    CACHE_EXPIRE_SECONDS: int = 300
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保数据目录存在
        self.BASE_DIR.mkdir(parents=True, exist_ok=True)
        
        # 设置默认文件路径
        if self.KEYWORDS_FILE is None:
            self.KEYWORDS_FILE = self.BASE_DIR / "keywords.json"
        if self.RESPONSES_FILE is None:
            self.RESPONSES_FILE = self.BASE_DIR / "responses.json"
    
    def validate(self) -> bool:
        """验证配置有效性"""
        # 检查阈值范围
        for name, value in [
            ("LEVEL_1_THRESHOLD", self.LEVEL_1_THRESHOLD),
            ("LEVEL_2_THRESHOLD", self.LEVEL_2_THRESHOLD),
            ("LEVEL_3_THRESHOLD", self.LEVEL_3_THRESHOLD),
        ]:
            if not (0 <= value <= 1):
                logger.error(f"{name} 超出范围 [0, 1]：{value}")
                return False
        
        # 检查阈值顺序
        if self.LEVEL_1_THRESHOLD > self.LEVEL_2_THRESHOLD:
            logger.error("LEVEL_1_THRESHOLD 不应大于 LEVEL_2_THRESHOLD")
            return False
        if self.LEVEL_2_THRESHOLD > self.LEVEL_3_THRESHOLD:
            logger.error("LEVEL_2_THRESHOLD 不应大于 LEVEL_3_THRESHOLD")
            return False
        
        # 检查 PHQ-9 分数范围（0-27）
        if not (0 <= self.PHQ9_WARNING_SCORE <= 27):
            logger.error(f"PHQ9_WARNING_SCORE 超出范围 [0, 27]：{self.PHQ9_WARNING_SCORE}")
            return False
        if not (0 <= self.PHQ9_CRITICAL_SCORE <= 27):
            logger.error(f"PHQ9_CRITICAL_SCORE 超出范围 [0, 27]：{self.PHQ9_CRITICAL_SCORE}")
            return False
        
        # 检查数据文件
        if self.KEYWORDS_FILE and not self.KEYWORDS_FILE.exists():
            logger.warning(f"关键词文件不存在：{self.KEYWORDS_FILE}")
        if self.RESPONSES_FILE and not self.RESPONSES_FILE.exists():
            logger.warning(f"响应文件不存在：{self.RESPONSES_FILE}")
        
        return True
    
    @classmethod
    def load(cls) -> "CrisisConfig":
        """加载配置（可从环境变量覆盖）"""
        config = cls()
        
        # 从环境变量覆盖布尔值
        config.ENABLE_TEXT_DETECTION = os.getenv("CRISIS_ENABLE_TEXT", "true").lower() == "true"
        config.ENABLE_VOICE_DETECTION = os.getenv("CRISIS_ENABLE_VOICE", "true").lower() == "true"
        config.ENABLE_SCALE_DETECTION = os.getenv("CRISIS_ENABLE_SCALE", "true").lower() == "true"
        config.USE_AI_GENERATION = os.getenv("CRISIS_USE_AI", "true").lower() == "true"
        config.ENABLE_RESOURCES = os.getenv("CRISIS_ENABLE_RESOURCES", "false").lower() == "true"
        
        # 从环境变量覆盖阈值（使用类定义中的默认值）
        config.LEVEL_1_THRESHOLD = float(os.getenv("CRISIS_LEVEL1", str(config.LEVEL_1_THRESHOLD)))
        config.LEVEL_2_THRESHOLD = float(os.getenv("CRISIS_LEVEL2", str(config.LEVEL_2_THRESHOLD)))
        config.LEVEL_3_THRESHOLD = float(os.getenv("CRISIS_LEVEL3", str(config.LEVEL_3_THRESHOLD)))
        
        # 从环境变量覆盖量表分数
        config.PHQ9_WARNING_SCORE = int(os.getenv("CRISIS_PHQ9_WARNING", "10"))
        config.PHQ9_CRITICAL_SCORE = int(os.getenv("CRISIS_PHQ9_CRITICAL", "20"))
        
        # 从环境变量覆盖超时
        config.AI_GENERATOR_TIMEOUT = int(os.getenv("CRISIS_AI_TIMEOUT", "5"))
        
        return config


# 全局配置单例
_config: Optional[CrisisConfig] = None


def get_config() -> CrisisConfig:
    """获取全局配置单例"""
    global _config
    if _config is None:
        _config = CrisisConfig.load()
        _config.validate()
    return _config


def reload_config() -> CrisisConfig:
    """重新加载配置"""
    global _config
    _config = CrisisConfig.load()
    _config.validate()
    return _config