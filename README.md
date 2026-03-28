# 元气充能陪伴平台

一个基于AI的智能情绪健康评估与疗愈系统，整合了多种心理评估量表、情感分析、MindChat对话疗愈和危机检测功能。

## 功能特性

### 1. 心理评估量表
- **PHQ-9** - 抑郁症筛查量表
- **GAD-7** - 焦虑症筛查量表
- **PSS-10** - 心理压力量表
- **综合评估** - 多量表联合评估

### 2. AI智能对话
- **MindChat对话系统** - 基于Qwen2的中文心理疗愈对话模型
- **个性化策略** - 根据用户画像提供定制化疗愈策略
- **多媒体疗愈** - 支持音乐、视频推荐
- **危机检测** - 自动识别并响应危机情况

### 3. 多模态情绪分析
- **文本情绪分析** - RoBERTa中文情感分析
- **语音情绪识别** - 基于音频特征的情绪分析
- **语音交互** - Whisper语音识别 + Edge-TTS语音合成

### 4. 数据分析与报告
- **趋势分析** - 情绪变化趋势图表
- **诊断报告** - 详细的评估结果报告
- **策略管理** - 个性化疗愈策略管理

## 技术栈

- **后端框架**: Flask + Flask-Login + SQLAlchemy
- **AI模型**:
  - Qwen2-1.5B-Instruct (MindChat对话)
  - RoBERTa-finetuned-dianping (情感分析)
  - Whisper Tiny (语音识别)
- **前端**: HTML + CSS + JavaScript (原生)
- **数据库**: SQLite
- **其他**: Plotly (可视化), edge-tts (语音合成)

## 项目结构

```
元气充能陪伴/
├── flask_app.py              # Flask主应用
├── models.py                 # 数据库模型
├── assessment_scales.py      # 量表评估模块
├── mindchat_dialogue.py      # MindChat对话系统
├── mindchat_model.py         # MindChat模型封装
├── whisper_asr.py            # Whisper语音识别
├── voice_module.py           # 语音模块(ASR+TTS)
├── multimodal_sentiment.py   # 多模态情绪分析
├── text_sentiment.py         # 文本情绪分析
├── crisis_detection/         # 危机检测模块
├── templates/                # HTML模板
├── static/                   # 静态资源(CSS/JS)
├── models/                   # AI模型文件(不提交)
├── instance/                 # 数据库实例(不提交)
└── requirements.txt          # 依赖包列表
```

## 安装与运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载模型

需要下载以下模型到 `models/` 目录：

1. **Qwen2-1.5B-Instruct** (MindChat对话模型)
2. **RoBERTa-finetuned-dianping-chinese** (情感分析模型)
3. **Whisper Tiny** (语音识别模型会自动下载)

### 3. 初始化数据库

首次运行会自动创建SQLite数据库。

### 4. 启动应用

```bash
python flask_app.py
```

访问 http://localhost:5000

## 使用说明

### 注册与登录
- 首次使用需要注册账户
- 支持用户名+密码登录

### 心理评估
- 选择量表进行测试(PHQ-9/GAD-7/PSS-10)
- 查看评估结果和建议
- 进行综合评估获得全面分析

### AI对话
- 与MindChat疗愈机器人对话
- 支持文字和语音输入
- 获取个性化疗愈建议

### 趋势分析
- 查看历史评估数据
- 分析情绪变化趋势
- 导出评估报告

## 配置说明

### 数据库配置
默认使用SQLite，数据库文件位于 `instance/mental_health.db`

### 模型路径配置
在 `flask_app.py` 中配置模型路径：
```python
mindchat_model_path = "./models/qwen2-1.5b-instruct"
sentiment_model_path = "./models/roberta-base-finetuned-dianping-chinese"
```

## 注意事项

1. **模型文件**: 模型文件较大(~3.7GB)，未包含在仓库中，需单独下载
2. **数据库**: `.db` 文件已添加到 `.gitignore`，不会被提交
3. **隐私保护**: 用户数据仅存储在本地，不会上传到云端
4. **医疗声明**: 本系统仅供参考，不能替代专业医疗诊断

## 开发环境

- Python 3.8+
- Flask 3.0+
- PyTorch 2.0+
- Transformers 4.30+

## 许可证

本项目仅供学习和研究使用。

## 致谢

- Qwen2模型由阿里云开发
- RoBERTa中文模型由Hugging Face社区提供
- Whisper由OpenAI开发
- edge-tts由微软开发

---

**版本**: 1.0.0
**最后更新**: 2026-03-28
