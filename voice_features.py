"""
语音特征提取模块 - 用于心理健康评估

功能:
1. 基频(F0)特征: 平均音高、音高标准差
2. 语速特征: 每秒音节数/词数
3. 能量特征: RMS能量(音量)
4. 颤音特征: 基频变化率

心理学意义:
- 低音高 + 低音量 = 抑郁倾向
- 高语速 = 焦虑倾向
- 高音高标准差 = 情绪不稳定
- 高颤音 = 情绪波动大
"""

import os
import sys
import warnings
from typing import Dict, Optional
import numpy as np

warnings.filterwarnings("ignore")


def extract_audio_features(audio_file_path: str) -> Dict:
    """
    提取音频特征用于心理健康评估

    Args:
        audio_file_path: 音频文件路径 (支持 wav, mp3, flac, m4a 等格式)

    Returns:
        特征字典:
        {
            'pitch_mean': float,      # 平均基频(Hz) - 低音高=抑郁倾向
            'pitch_std': float,       # 基频标准差 - 高标准差=情绪不稳定
            'tempo': float,           # 语速(音节/秒) - 高语速=焦虑倾向
            'energy': float,          # RMS能量 - 低能量=抑郁倾向
            'shimmer': float,         # 颤音指标(基频变化率) - 高颤音=情绪不稳定
            'duration': float,        # 音频时长(秒)
            'success': bool,          # 提取是否成功
            'error': str              # 错误信息(如果失败)
        }
    """
    # 检查文件是否存在
    if not os.path.exists(audio_file_path):
        return {
            'pitch_mean': 0.0,
            'pitch_std': 0.0,
            'tempo': 0.0,
            'energy': 0.0,
            'shimmer': 0.0,
            'duration': 0.0,
            'success': False,
            'error': f'文件不存在: {audio_file_path}'
        }

    # 尝试使用librosa提取特征
    try:
        return _extract_with_librosa(audio_file_path)
    except ImportError:
        # librosa未安装，使用标准库方法
        print('[WARNING] librosa未安装，使用简化特征提取')
        print('         推荐安装: pip install librosa')
        return _extract_with_stdlib(audio_file_path)
    except Exception as e:
        return {
            'pitch_mean': 0.0,
            'pitch_std': 0.0,
            'tempo': 0.0,
            'energy': 0.0,
            'shimmer': 0.0,
            'duration': 0.0,
            'success': False,
            'error': f'特征提取失败: {str(e)}'
        }


def _extract_with_librosa(audio_file_path: str) -> Dict:
    """
    使用librosa提取完整音频特征

    Args:
        audio_file_path: 音频文件路径

    Returns:
        特征字典
    """
    import librosa

    # 加载音频
    y, sr = librosa.load(audio_file_path, sr=22050)

    # 1. 音频时长
    duration = float(librosa.get_duration(y=y, sr=sr))

    # 2. 提取基频(F0) - 使用pyin算法(更准确)
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y,
        fmin=librosa.note_to_hz('C2'),   # 最低音高 ~65Hz
        fmax=librosa.note_to_hz('C7'),   # 最高音高 ~2093Hz
        sr=sr
    )

    # 过滤有效的基频值
    valid_f0 = f0[~np.isnan(f0)]

    if len(valid_f0) > 0:
        pitch_mean = float(np.mean(valid_f0))
        pitch_std = float(np.std(valid_f0))

        # 计算颤音(shimmer) - 基频的局部变化率
        # 使用相邻帧的基频差分
        f0_diff = np.diff(valid_f0)
        shimmer = float(np.mean(np.abs(f0_diff)) / (pitch_mean + 1e-8))  # 归一化
    else:
        pitch_mean = 0.0
        pitch_std = 0.0
        shimmer = 0.0

    # 3. RMS能量(音量)
    rms = librosa.feature.rms(y=y)[0]
    energy = float(np.mean(rms))

    # 4. 语速估计 - 基于节拍和onset检测
    # 方法1: 检测onset(音节/词的开始)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    # tempo可能是numpy数组,转换为标量
    if hasattr(tempo, 'item'):
        tempo = float(tempo.item())
    else:
        tempo = float(tempo)

    # 方法2: 统计onset数量作为语速指标
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    if duration > 0 and len(onsets) > 0:
        # 每秒onset数量作为语速
        speech_rate = len(onsets) / duration
    else:
        speech_rate = 0.0

    # 使用BPM归一化的语速(60 BPM = 1 音节/秒)
    tempo_normalized = tempo / 60.0

    # 综合两种方法
    estimated_tempo = (tempo_normalized + speech_rate) / 2.0

    return {
        'pitch_mean': round(pitch_mean, 2),
        'pitch_std': round(pitch_std, 2),
        'tempo': round(estimated_tempo, 2),
        'energy': round(energy, 4),
        'shimmer': round(shimmer, 6),
        'duration': round(duration, 2),
        'success': True,
        'error': None
    }


def _extract_with_stdlib(audio_file_path: str) -> Dict:
    """
    使用Python标准库提取简化音频特征
    (当librosa不可用时的备用方案)

    Args:
        audio_file_path: 音频文件路径

    Returns:
        特征字典
    """
    import wave
    import struct

    try:
        # 尝试读取WAV文件
        if audio_file_path.lower().endswith('.wav'):
            return _extract_wav_stdlib(audio_file_path)
        else:
            return {
                'pitch_mean': 0.0,
                'pitch_std': 0.0,
                'tempo': 0.0,
                'energy': 0.0,
                'shimmer': 0.0,
                'duration': 0.0,
                'success': False,
                'error': '标准库仅支持WAV格式，请安装librosa: pip install librosa'
            }
    except Exception as e:
        return {
            'pitch_mean': 0.0,
            'pitch_std': 0.0,
            'tempo': 0.0,
            'energy': 0.0,
            'shimmer': 0.0,
            'duration': 0.0,
            'success': False,
            'error': f'标准库提取失败: {str(e)}'
        }


def _extract_wav_stdlib(wav_file_path: str) -> Dict:
    """
    使用wave模块提取WAV文件的基本特征

    Args:
        wav_file_path: WAV文件路径

    Returns:
        特征字典
    """
    try:
        with wave.open(wav_file_path, 'rb') as wav_file:
            # 获取音频参数
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            sampwidth = wav_file.getsampwidth()
            duration = frames / float(rate)

            # 读取音频数据
            frame_data = wav_file.readframes(frames)

        # 解析PCM数据 (在with块外,但保存了sampwidth)
        if sampwidth == 2:  # 16-bit
            fmt = '<{}h'.format(len(frame_data) // 2)
            data = np.array(struct.unpack(fmt, frame_data), dtype=np.int16)
        elif sampwidth == 4:  # 32-bit
            fmt = '<{}i'.format(len(frame_data) // 4)
            data = np.array(struct.unpack(fmt, frame_data), dtype=np.int32)
        else:
            raise ValueError(f"不支持的位深度: {sampwidth}")

        # 归一化到[-1, 1]
        data = data.astype(np.float32) / np.max(np.abs(data))

        # 1. 计算能量(RMS)
        energy = float(np.sqrt(np.mean(data ** 2)))

        # 2. 简化的基频估计 - 基于零交叉率
        # 零交叉率与基频相关但不准确
        zero_crossings = np.sum(np.abs(np.diff(np.sign(data)))) / 2
        zero_crossing_rate = zero_crossings / len(data)

        # 粗略估计基频(假设零交叉率 ≈ 2 * 基频)
        estimated_f0 = zero_crossing_rate * rate / 2

        pitch_mean = float(estimated_f0) if estimated_f0 > 50 else 0.0
        pitch_std = pitch_mean * 0.2  # 假设20%变化(简化)

        # 3. 颤音(简化)
        shimmer = pitch_std / (pitch_mean + 1e-8)

        # 4. 语速(无法准确估计，返回0)
        tempo = 0.0

        return {
            'pitch_mean': round(pitch_mean, 2),
            'pitch_std': round(pitch_std, 2),
            'tempo': round(tempo, 2),
            'energy': round(energy, 4),
            'shimmer': round(shimmer, 6),
            'duration': round(duration, 2),
            'success': True,
            'error': None,
            'note': '标准库简化提取，建议安装librosa获得准确结果'
        }

    except Exception as e:
        return {
            'pitch_mean': 0.0,
            'pitch_std': 0.0,
            'tempo': 0.0,
            'energy': 0.0,
            'shimmer': 0.0,
            'duration': 0.0,
            'success': False,
            'error': f'WAV解析失败: {str(e)}'
        }


def interpret_features(features: Dict) -> Dict:
    """
    解读音频特征的心理学意义

    Args:
        features: extract_audio_features()返回的特征字典

    Returns:
        解读结果:
        {
            'depression_risk': str,      # 抑郁风险
            'anxiety_risk': str,         # 焦虑风险
            'emotional_stability': str,  # 情绪稳定性
            'confidence': float          # 置信度
        }
    """
    if not features.get('success', False):
        return {
            'depression_risk': '未知',
            'anxiety_risk': '未知',
            'emotional_stability': '未知',
            'confidence': 0.0
        }

    risk_scores = {
        'depression': 0.0,
        'anxiety': 0.0,
        'instability': 0.0
    }

    # 1. 低音高 = 抑郁倾向 (正常说话: 150-250Hz)
    pitch_mean = features.get('pitch_mean', 0)
    if pitch_mean > 0:
        if pitch_mean < 120:
            risk_scores['depression'] += 0.4
        elif pitch_mean < 150:
            risk_scores['depression'] += 0.2

    # 2. 低能量 = 抑郁倾向
    energy = features.get('energy', 0)
    if energy < 0.05:
        risk_scores['depression'] += 0.4
    elif energy < 0.1:
        risk_scores['depression'] += 0.2

    # 3. 高语速 = 焦虑倾向 (正常: 3-5 音节/秒)
    tempo = features.get('tempo', 0)
    if tempo > 6.0:
        risk_scores['anxiety'] += 0.5
    elif tempo > 5.0:
        risk_scores['anxiety'] += 0.3

    # 4. 高音高标准差 = 情绪不稳定
    pitch_std = features.get('pitch_std', 0)
    if pitch_std > 50:
        risk_scores['instability'] += 0.4
    elif pitch_std > 30:
        risk_scores['instability'] += 0.2

    # 5. 高颤音 = 情绪波动
    shimmer = features.get('shimmer', 0)
    if shimmer > 0.3:
        risk_scores['instability'] += 0.4
    elif shimmer > 0.2:
        risk_scores['instability'] += 0.2

    # 判定风险等级
    def get_risk_level(score):
        if score >= 0.7:
            return '高风险'
        elif score >= 0.4:
            return '中等风险'
        elif score >= 0.2:
            return '低风险'
        else:
            return '正常'

    return {
        'depression_risk': get_risk_level(risk_scores['depression']),
        'anxiety_risk': get_risk_level(risk_scores['anxiety']),
        'emotional_stability': get_risk_level(risk_scores['instability']),
        'confidence': round(max(risk_scores.values()), 2),
        'risk_scores': {
            'depression': round(risk_scores['depression'], 2),
            'anxiety': round(risk_scores['anxiety'], 2),
            'instability': round(risk_scores['instability'], 2)
        }
    }


# ==================== 便捷函数 ====================

def analyze_voice_for_mental_health(audio_file_path: str) -> Dict:
    """
    完整的语音心理健康分析流程

    Args:
        audio_file_path: 音频文件路径

    Returns:
        完整分析报告:
        {
            'features': Dict,      # 原始特征
            'interpretation': Dict # 解读结果
        }
    """
    features = extract_audio_features(audio_file_path)
    interpretation = interpret_features(features)

    return {
        'features': features,
        'interpretation': interpretation
    }


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("语音特征提取模块测试".center(70))
    print("=" * 70)

    if len(sys.argv) > 1:
        # 命令行指定音频文件
        audio_path = sys.argv[1]
    else:
        # 默认测试文件
        audio_path = "test_audio.wav"
        print(f"\n[提示] 可通过命令行指定音频: python voice_features.py <音频文件路径>")
        print(f"[提示] 使用默认测试文件: {audio_path}\n")

    if not os.path.exists(audio_path):
        print(f"[ERROR] 音频文件不存在: {audio_path}")
        print("\n请提供有效的音频文件路径")
        print("支持格式: WAV, MP3, FLAC, M4A (需安装librosa)")
        sys.exit(1)

    print(f"\n[分析] 正在提取音频特征...")
    print(f"文件: {audio_path}")
    print("-" * 70)

    # 提取特征
    features = extract_audio_features(audio_path)

    if features['success']:
        print("\n[OK] 特征提取成功!\n")
        print("原始特征:")
        print(f"  - 平均基频: {features['pitch_mean']} Hz")
        print(f"  - 基频标准差: {features['pitch_std']} Hz")
        print(f"  - 语速: {features['tempo']} 音节/秒")
        print(f"  - RMS能量: {features['energy']}")
        print(f"  - 颤音指标: {features['shimmer']}")
        print(f"  - 音频时长: {features['duration']} 秒")

        # 心理学解读
        print("\n" + "-" * 70)
        print("\n[解读] 心理健康风险评估:\n")

        interpretation = interpret_features(features)

        print(f"  抑郁风险: {interpretation['depression_risk']}")
        print(f"  焦虑风险: {interpretation['anxiety_risk']}")
        print(f"  情绪稳定性: {interpretation['emotional_stability']}")
        print(f"  分析置信度: {interpretation['confidence']}")

        if 'risk_scores' in interpretation:
            print(f"\n  风险评分:")
            print(f"    - 抑郁倾向: {interpretation['risk_scores']['depression']}")
            print(f"    - 焦虑倾向: {interpretation['risk_scores']['anxiety']}")
            print(f"    - 情绪不稳定: {interpretation['risk_scores']['instability']}")

        print("\n" + "=" * 70)
        print("分析完成!".center(70))
        print("=" * 70)

    else:
        print(f"\n[ERROR] 特征提取失败: {features['error']}")
        sys.exit(1)
