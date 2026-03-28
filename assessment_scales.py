"""
心理评估量表系统
包含 PHQ-9、ABC、CARS、HAMD 四种专业心理评估量表
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import json


# ==================== PHQ-9 量表（抑郁症筛查）====================

PHQ9_QUESTIONS = [
    {
        "id": 1,
        "question": "做事时提不起劲或没有兴趣",
        "options": [
            {"value": 0, "text": "完全不会"},
            {"value": 1, "text": "几天"},
            {"value": 2, "text": "一半以上的天数"},
            {"value": 3, "text": "几乎每天"}
        ]
    },
    {
        "id": 2,
        "question": "心情低落、沮丧或绝望",
        "options": [
            {"value": 0, "text": "完全不会"},
            {"value": 1, "text": "几天"},
            {"value": 2, "text": "一半以上的天数"},
            {"value": 3, "text": "几乎每天"}
        ]
    },
    {
        "id": 3,
        "question": "入睡困难、睡不着或睡眠过多",
        "options": [
            {"value": 0, "text": "完全不会"},
            {"value": 1, "text": "几天"},
            {"value": 2, "text": "一半以上的天数"},
            {"value": 3, "text": "几乎每天"}
        ]
    },
    {
        "id": 4,
        "question": "感觉疲倦或没有活力",
        "options": [
            {"value": 0, "text": "完全不会"},
            {"value": 1, "text": "几天"},
            {"value": 2, "text": "一半以上的天数"},
            {"value": 3, "text": "几乎每天"}
        ]
    },
    {
        "id": 5,
        "question": "食欲不振或吃得太多",
        "options": [
            {"value": 0, "text": "完全不会"},
            {"value": 1, "text": "几天"},
            {"value": 2, "text": "一半以上的天数"},
            {"value": 3, "text": "几乎每天"}
        ]
    },
    {
        "id": 6,
        "question": "觉得自己很糟，或觉得自己很失败，让自己或家人失望",
        "options": [
            {"value": 0, "text": "完全不会"},
            {"value": 1, "text": "几天"},
            {"value": 2, "text": "一半以上的天数"},
            {"value": 3, "text": "几乎每天"}
        ]
    },
    {
        "id": 7,
        "question": "对事物专注有困难，例如阅读报纸或看电视时",
        "options": [
            {"value": 0, "text": "完全不会"},
            {"value": 1, "text": "几天"},
            {"value": 2, "text": "一半以上的天数"},
            {"value": 3, "text": "几乎每天"}
        ]
    },
    {
        "id": 8,
        "question": "动作或说话速度缓慢到别人已经察觉？或相反，烦躁或坐立不安、动来动去",
        "options": [
            {"value": 0, "text": "完全不会"},
            {"value": 1, "text": "几天"},
            {"value": 2, "text": "一半以上的天数"},
            {"value": 3, "text": "几乎每天"}
        ]
    },
    {
        "id": 9,
        "question": "有不如死掉或用某种方式伤害自己的念头",
        "options": [
            {"value": 0, "text": "完全不会"},
            {"value": 1, "text": "几天"},
            {"value": 2, "text": "一半以上的天数"},
            {"value": 3, "text": "几乎每天"}
        ]
    }
]


def calculate_phq9_score(answers: Dict[int, int]) -> Dict[str, Any]:
    """
    计算 PHQ-9 量表分数

    Args:
        answers: 问题答案字典 {问题ID: 得分}

    Returns:
        包含总分、严重程度和建议的字典
    """
    total_score = sum(answers.values())

    # 判断严重程度
    if total_score <= 4:
        severity = "无抑郁"
        level = "minimal"
        recommendation = "您的心理健康状况良好，继续保持！"
    elif total_score <= 9:
        severity = "轻度抑郁"
        level = "mild"
        recommendation = "您可能有轻度抑郁症状，建议多关注自己的情绪状态，适当放松。"
    elif total_score <= 14:
        severity = "中度抑郁"
        level = "moderate"
        recommendation = "您可能有中度抑郁症状，建议寻求专业心理咨询师的帮助。"
    elif total_score <= 19:
        severity = "中重度抑郁"
        level = "moderately_severe"
        recommendation = "您可能有中重度抑郁症状，强烈建议寻求专业心理医生的帮助。"
    else:
        severity = "重度抑郁"
        level = "severe"
        recommendation = "您可能有重度抑郁症状，请务必寻求专业心理医生的帮助！"

    return {
        "scale_name": "PHQ-9",
        "total_score": total_score,
        "max_score": 27,
        "severity": severity,
        "level": level,
        "recommendation": recommendation,
        "answers": answers
    }


# ==================== ABC 量表（自闭症行为检查表）====================

ABC_QUESTIONS = [
    {
        "id": 1,
        "question": "对周围环境或事物缺乏兴趣",
        "options": [
            {"value": 0, "text": "从不"},
            {"value": 1, "text": "偶尔"},
            {"value": 2, "text": "经常"},
            {"value": 3, "text": "总是"}
        ]
    },
    {
        "id": 2,
        "question": "不能恰当地注视物体或人",
        "options": [
            {"value": 0, "text": "从不"},
            {"value": 1, "text": "偶尔"},
            {"value": 2, "text": "经常"},
            {"value": 3, "text": "总是"}
        ]
    },
    {
        "id": 3,
        "question": "刻板或重复的动作（如摇摆、旋转手或物体、搓手等）",
        "options": [
            {"value": 0, "text": "从不"},
            {"value": 1, "text": "偶尔"},
            {"value": 2, "text": "经常"},
            {"value": 3, "text": "总是"}
        ]
    },
    {
        "id": 4,
        "question": "对常规改变感到不安",
        "options": [
            {"value": 0, "text": "从不"},
            {"value": 1, "text": "偶尔"},
            {"value": 2, "text": "经常"},
            {"value": 3, "text": "总是"}
        ]
    },
    {
        "id": 5,
        "question": "社交互动困难（不会交朋友、不理解社交规则）",
        "options": [
            {"value": 0, "text": "从不"},
            {"value": 1, "text": "偶尔"},
            {"value": 2, "text": "经常"},
            {"value": 3, "text": "总是"}
        ]
    },
    {
        "id": 6,
        "question": "语言发育迟缓或语言异常",
        "options": [
            {"value": 0, "text": "从不"},
            {"value": 1, "text": "偶尔"},
            {"value": 2, "text": "经常"},
            {"value": 3, "text": "总是"}
        ]
    },
    {
        "id": 7,
        "question": "模仿言语（重复他人的话）或不正常的声音",
        "options": [
            {"value": 0, "text": "从不"},
            {"value": 1, "text": "偶尔"},
            {"value": 2, "text": "经常"},
            {"value": 3, "text": "总是"}
        ]
    },
    {
        "id": 8,
        "question": "对疼痛、温度等感觉反应异常",
        "options": [
            {"value": 0, "text": "从不"},
            {"value": 1, "text": "偶尔"},
            {"value": 2, "text": "经常"},
            {"value": 3, "text": "总是"}
        ]
    },
    {
        "id": 9,
        "question": "注意力不集中或容易分心",
        "options": [
            {"value": 0, "text": "从不"},
            {"value": 1, "text": "偶尔"},
            {"value": 2, "text": "经常"},
            {"value": 3, "text": "总是"}
        ]
    },
    {
        "id": 10,
        "question": "对特定物体或活动有异常强烈的依恋",
        "options": [
            {"value": 0, "text": "从不"},
            {"value": 1, "text": "偶尔"},
            {"value": 2, "text": "经常"},
            {"value": 3, "text": "总是"}
        ]
    }
]


def calculate_abc_score(answers: Dict[int, int]) -> Dict[str, Any]:
    """
    计算 ABC 量表分数

    Args:
        answers: 问题答案字典 {问题ID: 得分}

    Returns:
        包含总分、严重程度和建议的字典
    """
    total_score = sum(answers.values())
    max_score = len(ABC_QUESTIONS) * 3

    # 判断严重程度
    percentage = (total_score / max_score) * 100

    if percentage <= 20:
        severity = "无明显自闭症特征"
        level = "normal"
        recommendation = "未发现明显的自闭症特征，发育状况良好。"
    elif percentage <= 40:
        severity = "轻度自闭症特征"
        level = "mild"
        recommendation = "存在一些自闭症特征，建议进一步观察和发展社交能力。"
    elif percentage <= 60:
        severity = "中度自闭症特征"
        level = "moderate"
        recommendation = "存在较明显的自闭症特征，建议寻求专业评估和干预。"
    else:
        severity = "重度自闭症特征"
        level = "severe"
        recommendation = "存在明显的自闭症特征，强烈建议寻求专业医疗评估和早期干预！"

    return {
        "scale_name": "ABC",
        "total_score": total_score,
        "max_score": max_score,
        "percentage": round(percentage, 1),
        "severity": severity,
        "level": level,
        "recommendation": recommendation,
        "answers": answers
    }


# ==================== CARS 量表（儿童自闭症评定量表）====================

CARS_QUESTIONS = [
    {
        "id": 1,
        "question": "人际关系",
        "description": "与他人的互动方式和质量",
        "options": [
            {"value": 1, "text": "年龄适当，与同龄人正常互动"},
            {"value": 2, "text": "轻微异常，有时避免眼神接触"},
            {"value": 3, "text": "中度异常，被动接受互动"},
            {"value": 4, "text": "严重异常，完全避免互动"}
        ]
    },
    {
        "id": 2,
        "question": "模仿能力",
        "description": "模仿言语和动作的能力",
        "options": [
            {"value": 1, "text": "年龄适当，能正常模仿"},
            {"value": 2, "text": "轻微异常，偶尔模仿"},
            {"value": 3, "text": "中度异常，模仿简单动作"},
            {"value": 4, "text": "严重异常，几乎不模仿"}
        ]
    },
    {
        "id": 3,
        "question": "情感反应",
        "description": "情感表达和反应的适当性",
        "options": [
            {"value": 1, "text": "年龄适当，情感反应正常"},
            {"value": 2, "text": "轻微异常，情感反应有时不当"},
            {"value": 3, "text": "中度异常，情感反应明显不当"},
            {"value": 4, "text": "严重异常，情感反应极度不当或平淡"}
        ]
    },
    {
        "id": 4,
        "question": "肢体运用能力",
        "description": "协调性和肢体动作的控制",
        "options": [
            {"value": 1, "text": "年龄适当，肢体协调"},
            {"value": 2, "text": "轻微异常，有些笨拙"},
            {"value": 3, "text": "中度异常，动作不协调"},
            {"value": 4, "text": "严重异常，肢体动作明显异常"}
        ]
    },
    {
        "id": 5,
        "question": "感官反应",
        "description": "对感官刺激的反应",
        "options": [
            {"value": 1, "text": "年龄适当，反应正常"},
            {"value": 2, "text": "轻微异常，对某些刺激过度或不足反应"},
            {"value": 3, "text": "中度异常，感官反应明显异常"},
            {"value": 4, "text": "严重异常，感官反应极度异常"}
        ]
    },
    {
        "id": 6,
        "question": "焦虑反应",
        "description": "面对新环境或变化时的反应",
        "options": [
            {"value": 1, "text": "年龄适当，反应正常"},
            {"value": 2, "text": "轻微异常，有时焦虑"},
            {"value": 3, "text": "中度异常，经常焦虑"},
            {"value": 4, "text": "严重异常，持续高度焦虑"}
        ]
    },
    {
        "id": 7,
        "question": "言语交流",
        "description": "语言发展和交流能力",
        "options": [
            {"value": 1, "text": "年龄适当，语言正常"},
            {"value": 2, "text": "轻微异常，语言发育稍迟缓"},
            {"value": 3, "text": "中度异常，语言明显迟缓"},
            {"value": 4, "text": "严重异常，几乎没有语言"}
        ]
    },
    {
        "id": 8,
        "question": "非言语交流",
        "description": "眼神、表情、手势等交流能力",
        "options": [
            {"value": 1, "text": "年龄适当，正常使用"},
            {"value": 2, "text": "轻微异常，有时不使用"},
            {"value": 3, "text": "中度异常，很少使用"},
            {"value": 4, "text": "严重异常，几乎不使用"}
        ]
    },
    {
        "id": 9,
        "question": "活动水平",
        "description": "活动的活跃度和适当性",
        "options": [
            {"value": 1, "text": "年龄适当，活动正常"},
            {"value": 2, "text": "轻微异常，活动稍多或稍少"},
            {"value": 3, "text": "中度异常，活动明显异常"},
            {"value": 4, "text": "严重异常，活动极度异常"}
        ]
    },
    {
        "id": 10,
        "question": "智力功能",
        "description": "认知和智力表现",
        "options": [
            {"value": 1, "text": "年龄适当，智力正常"},
            {"value": 2, "text": "轻微异常，智力稍低"},
            {"value": 3, "text": "中度异常，智力明显低于同龄人"},
            {"value": 4, "text": "严重异常，智力严重受损"}
        ]
    },
    {
        "id": 11,
        "question": "刻板行为",
        "description": "重复性、固定性行为模式",
        "options": [
            {"value": 1, "text": "无或很少"},
            {"value": 2, "text": "轻微，偶尔有刻板行为"},
            {"value": 3, "text": "中度，经常有刻板行为"},
            {"value": 4, "text": "严重，持续明显的刻板行为"}
        ]
    },
    {
        "id": 12,
        "question": "对日常变化的适应",
        "description": "对常规和环境变化的适应能力",
        "options": [
            {"value": 1, "text": "年龄适当，适应正常"},
            {"value": 2, "text": "轻微异常，对变化有些抵抗"},
            {"value": 3, "text": "中度异常，对变化明显抵抗"},
            {"value": 4, "text": "严重异常，极度抗拒变化"}
        ]
    },
    {
        "id": 13,
        "question": "视觉反应",
        "description": "对视觉刺激的反应和关注",
        "options": [
            {"value": 1, "text": "年龄适当，反应正常"},
            {"value": 2, "text": "轻微异常，有时过度或不足关注"},
            {"value": 3, "text": "中度异常，视觉反应明显异常"},
            {"value": 4, "text": "严重异常，视觉反应极度异常"}
        ]
    },
    {
        "id": 14,
        "question": "听觉反应",
        "description": "对听觉刺激的反应和关注",
        "options": [
            {"value": 1, "text": "年龄适当，反应正常"},
            {"value": 2, "text": "轻微异常，有时对声音反应异常"},
            {"value": 3, "text": "中度异常，听觉反应明显异常"},
            {"value": 4, "text": "严重异常，听觉反应极度异常"}
        ]
    },
    {
        "id": 15,
        "question": "近感觉反应",
        "description": "对触觉、味觉、嗅觉等近感觉的反应",
        "options": [
            {"value": 1, "text": "年龄适当，反应正常"},
            {"value": 2, "text": "轻微异常，有时反应异常"},
            {"value": 3, "text": "中度异常，反应明显异常"},
            {"value": 4, "text": "严重异常，反应极度异常"}
        ]
    }
]


def calculate_cars_score(answers: Dict[int, int]) -> Dict[str, Any]:
    """
    计算 CARS 量表分数

    Args:
        answers: 问题答案字典 {问题ID: 得分}

    Returns:
        包含总分、严重程度和建议的字典
    """
    total_score = sum(answers.values())
    min_score = len(CARS_QUESTIONS) * 1
    max_score = len(CARS_QUESTIONS) * 4

    # 判断严重程度
    if total_score <= 15:
        severity = "非自闭症"
        level = "normal"
        recommendation = "未发现自闭症特征，发展状况正常。"
    elif total_score <= 29:
        severity = "轻度-中度自闭症"
        level = "mild_moderate"
        recommendation = "存在轻度至中度自闭症特征，建议寻求专业评估和干预支持。"
    elif total_score <= 36:
        severity = "中度自闭症"
        level = "moderate"
        recommendation = "存在中度自闭症特征，建议立即寻求专业评估和制定干预计划。"
    else:
        severity = "重度自闭症"
        level = "severe"
        recommendation = "存在重度自闭症特征，强烈建议寻求专业医疗评估和全面干预！"

    return {
        "scale_name": "CARS",
        "total_score": total_score,
        "min_score": min_score,
        "max_score": max_score,
        "severity": severity,
        "level": level,
        "recommendation": recommendation,
        "answers": answers
    }


# ==================== HAMD 量表（汉密尔顿抑郁量表）====================

HAMD_QUESTIONS = [
    {
        "id": 1,
        "question": "抑郁情绪",
        "description": "悲伤、绝望、无助等情绪",
        "options": [
            {"value": 0, "text": "无"},
            {"value": 1, "text": "仅在问及时表达"},
            {"value": 2, "text": "自发表达"},
            {"value": 3, "text": "通过言语和非言语持续表达"},
            {"value": 4, "text": "极度绝望和自责"}
        ]
    },
    {
        "id": 2,
        "question": "有罪感",
        "description": "自责、内疚感",
        "options": [
            {"value": 0, "text": "无"},
            {"value": 1, "text": "轻微自责"},
            {"value": 2, "text": "明显自责"},
            {"value": 3, "text": "严重的罪恶感和自责"},
            {"value": 4, "text": "极度自责，有罪恶妄想"}
        ]
    },
    {
        "id": 3,
        "question": "自杀",
        "description": "自杀意念和行为",
        "options": [
            {"value": 0, "text": "无"},
            {"value": 1, "text": "觉得活着没意思"},
            {"value": 2, "text": "希望已死或有自杀念头"},
            {"value": 3, "text": "有自杀准备"},
            {"value": 4, "text": "有自杀行为"}
        ]
    },
    {
        "id": 4,
        "question": "入睡困难",
        "description": "睡眠质量",
        "options": [
            {"value": 0, "text": "无困难"},
            {"value": 1, "text": "轻微困难"},
            {"value": 2, "text": "明显困难"}
        ]
    },
    {
        "id": 5,
        "question": "睡眠不深",
        "description": "睡眠深度和质量",
        "options": [
            {"value": 0, "text": "正常"},
            {"value": 1, "text": "轻微不安"},
            {"value": 2, "text": "明显不安，多梦"}
        ]
    },
    {
        "id": 6,
        "question": "早醒",
        "description": "醒后无法再入睡",
        "options": [
            {"value": 0, "text": "无"},
            {"value": 1, "text": "轻微早醒"},
            {"value": 2, "text": "明显早醒"}
        ]
    },
    {
        "id": 7,
        "question": "工作和活动",
        "description": "日常工作和活动能力",
        "options": [
            {"value": 0, "text": "正常"},
            {"value": 1, "text": "轻微下降"},
            {"value": 2, "text": "明显下降"},
            {"value": 3, "text": "严重下降"},
            {"value": 4, "text": "完全丧失工作能力"}
        ]
    },
    {
        "id": 8,
        "question": "迟缓",
        "description": "思维和言语迟缓",
        "options": [
            {"value": 0, "text": "无"},
            {"value": 1, "text": "轻微迟缓"},
            {"value": 2, "text": "明显迟缓"},
            {"value": 3, "text": "严重迟缓"},
            {"value": 4, "text": "极度迟缓，无法交流"}
        ]
    },
    {
        "id": 9,
        "question": "激越",
        "description": "焦虑不安、坐立难安",
        "options": [
            {"value": 0, "text": "无"},
            {"value": 1, "text": "轻微坐立不安"},
            {"value": 2, "text": "明显的搓手、咬指甲等"},
            {"value": 3, "text": "严重激越，无法静坐"},
            {"value": 4, "text": "极度激越，撕咬衣物等"}
        ]
    },
    {
        "id": 10,
        "question": "精神性焦虑",
        "description": "主观焦虑感",
        "options": [
            {"value": 0, "text": "无"},
            {"value": 1, "text": "轻微紧张"},
            {"value": 2, "text": "明显焦虑"},
            {"value": 3, "text": "严重焦虑"},
            {"value": 4, "text": "极度焦虑，惊恐发作"}
        ]
    },
    {
        "id": 11,
        "question": "躯体性焦虑",
        "description": "焦虑的生理表现",
        "options": [
            {"value": 0, "text": "无"},
            {"value": 1, "text": "轻微"},
            {"value": 2, "text": "中度"},
            {"value": 3, "text": "严重"},
            {"value": 4, "text": "极重度"}
        ]
    },
    {
        "id": 12,
        "question": "胃肠道症状",
        "description": "消化系统症状",
        "options": [
            {"value": 0, "text": "无"},
            {"value": 1, "text": "轻微"},
            {"value": 2, "text": "中度"}
        ]
    },
    {
        "id": 13,
        "question": "全身症状",
        "description": "头痛、背痛、肌肉酸痛等",
        "options": [
            {"value": 0, "text": "无"},
            {"value": 1, "text": "轻微"},
            {"value": 2, "text": "中度"}
        ]
    },
    {
        "id": 14,
        "question": "性症状",
        "description": "性欲减退或丧失",
        "options": [
            {"value": 0, "text": "无异常"},
            {"value": 1, "text": "轻度"},
            {"value": 2, "text": "重度"}
        ]
    },
    {
        "id": 15,
        "question": "疑病",
        "description": "过度担心健康",
        "options": [
            {"value": 0, "text": "无"},
            {"value": 1, "text": "过分关注身体"},
            {"value": 2, "text": "经常担心健康"},
            {"value": 3, "text": "持续疑病"},
            {"value": 4, "text": "疑病妄想"}
        ]
    },
    {
        "id": 16,
        "question": "体重减轻",
        "description": "体重变化情况",
        "options": [
            {"value": 0, "text": "无"},
            {"value": 1, "text": "可能有些体重下降"},
            {"value": 2, "text": "明确体重下降"}
        ]
    },
    {
        "id": 17,
        "question": "自知力",
        "description": "对疾病的认知",
        "options": [
            {"value": 0, "text": "有完整的自知力"},
            {"value": 1, "text": "自知力部分存在"},
            {"value": 2, "text": "无自知力"}
        ]
    }
]


def calculate_hamd_score(answers: Dict[int, int]) -> Dict[str, Any]:
    """
    计算 HAMD 量表分数（17项版本）

    Args:
        answers: 问题答案字典 {问题ID: 得分}

    Returns:
        包含总分、严重程度和建议的字典
    """
    total_score = sum(answers.values())
    max_score = 52  # 17项版本最大分

    # 判断严重程度（基于标准HAMD-17评分标准）
    if total_score <= 7:
        severity = "正常"
        level = "normal"
        recommendation = "您的心理健康状况良好，没有明显抑郁症状。"
    elif total_score <= 17:
        severity = "轻度抑郁"
        level = "mild"
        recommendation = "您可能有轻度抑郁症状，建议关注情绪健康，适当放松。"
    elif total_score <= 24:
        severity = "中度抑郁"
        level = "moderate"
        recommendation = "您可能有中度抑郁症状，建议寻求专业心理咨询师的帮助。"
    else:
        severity = "重度抑郁"
        level = "severe"
        recommendation = "您可能有重度抑郁症状，请务必寻求专业心理医生的帮助！"

    return {
        "scale_name": "HAMD-17",
        "total_score": total_score,
        "max_score": max_score,
        "severity": severity,
        "level": level,
        "recommendation": recommendation,
        "answers": answers
    }


# ==================== 量表管理器 ====================

class ScaleManager:
    """量表管理器，统一管理所有量表"""

    SCALE_INFO = {
        "phq9": {
            "name": "PHQ-9",
            "full_name": "患者健康问卷-9项",
            "description": "抑郁症筛查量表，适用于成人自评",
            "target_population": "成人",
            "questions": PHQ9_QUESTIONS,
            "calculator": calculate_phq9_score,
            "time_required": "约3-5分钟",
            "icon": "😔"
        },
        "abc": {
            "name": "ABC",
            "full_name": "自闭症行为检查表",
            "description": "自闭症谱系障碍筛查量表",
            "target_population": "儿童和青少年",
            "questions": ABC_QUESTIONS,
            "calculator": calculate_abc_score,
            "time_required": "约10-15分钟",
            "icon": "🧩"
        },
        "cars": {
            "name": "CARS",
            "full_name": "儿童自闭症评定量表",
            "description": "专业自闭症诊断评估量表",
            "target_population": "儿童（需专业人员评估）",
            "questions": CARS_QUESTIONS,
            "calculator": calculate_cars_score,
            "time_required": "约20-30分钟",
            "icon": "👶"
        },
        "hamd": {
            "name": "HAMD",
            "full_name": "汉密尔顿抑郁量表",
            "description": "专业抑郁症状评估量表",
            "target_population": "成人（需专业人员评估）",
            "questions": HAMD_QUESTIONS,
            "calculator": calculate_hamd_score,
            "time_required": "约15-20分钟",
            "icon": "📊"
        }
    }

    @classmethod
    def get_scale_info(cls, scale_id: str) -> Optional[Dict]:
        """获取量表信息"""
        return cls.SCALE_INFO.get(scale_id)

    @classmethod
    def get_all_scales(cls) -> Dict[str, Dict]:
        """获取所有量表信息"""
        return cls.SCALE_INFO

    @classmethod
    def calculate_score(cls, scale_id: str, answers: Dict[int, int]) -> Optional[Dict]:
        """计算量表分数"""
        scale_info = cls.get_scale_info(scale_id)
        if not scale_info:
            return None

        calculator = scale_info["calculator"]
        return calculator(answers)

    @classmethod
    def validate_answers(cls, scale_id: str, answers: Dict[int, int]) -> bool:
        """验证答案完整性"""
        scale_info = cls.get_scale_info(scale_id)
        if not scale_info:
            return False

        questions = scale_info["questions"]
        question_ids = {q["id"] for q in questions}

        # 检查是否所有问题都有答案
        return question_ids.issubset(answers.keys())


# ==================== 评估结果存储 ====================

class AssessmentResult:
    """评估结果类"""

    def __init__(self, scale_id: str, result: Dict, user_info: Optional[Dict] = None):
        self.scale_id = scale_id
        self.result = result
        self.user_info = user_info or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "scale_id": self.scale_id,
            "result": self.result,
            "user_info": self.user_info,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
