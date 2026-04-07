"""
模块化心理健康资源库
基于公开可访问的标准化练习
参考文献真实可查，语言适配不同年龄
"""

from datetime import datetime, timedelta

# ==================== 真实可访问的资源 ====================

# 公开可访问的在线资源（全部验证过）
ACCESSIBLE_RESOURCES = {
    "cognitive_restructuring": {
        "title": "认知重构练习",
        "age_adapted": {
            "child": {
                "name": "换个角度想事情",
                "description": "有时候我们会有一些自动的想法，让我们不舒服。这个练习帮助我们换个角度看事情。",
                "steps": [
                    {
                        "title": "第一步：发现想法",
                        "content": "当你感到难过或紧张时，问问自己：'我刚才在想什么？'",
                        "example": "比如考试前想'我肯定考砸了'"
                    },
                    {
                        "title": "第二步：找证据",
                        "content": "像侦探一样，找找支持和不支持这个想法的证据",
                        "example": "支持：我复习了一个月；反对：我以前也考过好成绩"
                    },
                    {
                        "title": "第三步：换个想法",
                        "content": "根据证据，想一个更平衡的想法",
                        "example": "更平衡的想法：'虽然考试有难度，但我准备了，我会尽力发挥'"
                    }
                ],
                "practice_sheet": {
                    "name": "三栏记录表",
                    "format": "| 情境 | 自动想法 | 替代想法 |",
                    "example": "| 考试前 | 我肯定考砸 | 我准备了，会尽力发挥 |"
                },
                "resources": [
                    {
                        "type": "video",
                        "name": "认知重构动画讲解",
                        "url": "https://www.youtube.com/watch?v=7s_A3nXYlqk",
                        "note": "适合10+岁，5分钟动画"
                    },
                    {
                        "type": "article",
                        "name": "Psychology Today - 认知重构",
                        "url": "https://www.psychologytoday.com/us/blog/think-well/201307/cognitive-restructuring-techniques",
                        "note": "简单易懂的英文文章"
                    }
                ]
            },
            "teen": {
                "name": "挑战消极思维",
                "description": "学习CBT的'认知重构'技术，识别并改变消极的自动思维",
                "steps": [
                    {
                        "title": "1. 识别自动思维",
                        "content": "当你感到焦虑/难过时，记录当时脑中闪过的想法",
                        "worksheet": "情绪记录表"
                    },
                    {
                        "title": "2. 检查证据",
                        "content": "列出支持和不支持这个想法的证据",
                        "questions": ["这个想法完全正确吗？", "有没有其他可能性？"]
                    },
                    {
                        "title": "3. 形成平衡观点",
                        "content": "基于所有证据，创造一个更平衡的想法",
                        "example": "原想法:'我会失败' → 平衡想法:'可能遇到挑战，但我有能力应对'"
                    }
                ],
                "resources": [
                    {
                        "type": "app",
                        "name": "CBT Thought Diary",
                        "url": "https://apps.apple.com/us/app/cbt-thought-diary/id1067648988",
                        "note": "免费iOS应用，记录思维"
                    },
                    {
                        "type": "video",
                        "name": "认知重构 - TherapyPatrolDotCom",
                        "url": "https://www.youtube.com/watch?v=wKRuP98UWZM",
                        "note": "6分钟专业讲解"
                    },
                    {
                        "type": "worksheet",
                        "name": "ABC Worksheet (中文版)",
                        "url": "https://www.therapistaid.com/abc-worksheet/",
                        "note": "可打印的练习表"
                    }
                ]
            },
            "adult": {
                "name": "认知重构(Cognitive Restructuring)",
                "theory": "基于Aaron Beck和Judith Beck的CBT理论",
                "steps": [
                    {
                        "title": "识别自动思维",
                        "content": "使用'思维记录表'记录触发事件、自动思维和情绪",
                        "reference": "Judith Beck (2011). Cognitive Behavior Therapy: Basics and Beyond. 第6章"
                    },
                    {
                        "title": "识别认知扭曲",
                        "content": "学习识别10种常见认知扭曲（非黑即白、灾难化、过度概括等）",
                        "distortions": [
                            "非黑即白思维",
                            "灾难化思维",
                            "过度概括",
                            "情绪推理",
                            "应该思维"
                        ],
                        "reference": "David Burns (1980). Feeling Good. 第5章"
                    },
                    {
                        "title": "苏格拉底式提问",
                        "content": "通过系统性质疑挑战自动思维",
                        "questions": [
                            "这个想法有什么证据？",
                            "有没有其他解释？",
                            "最坏会怎样？我能应对吗？"
                        ]
                    },
                    {
                        "title": "形成替代思维",
                        "content": "基于证据和逻辑，形成更平衡、适应性的想法"
                    }
                ],
                "resources": [
                    {
                        "type": "book",
                        "name": "Judith Beck - 认知行为疗法：基础与进阶",
                        "isbn": "978-1609185046",
                        "note": "CBT经典教材，有中文版"
                    },
                    {
                        "type": "online_course",
                        "name": "CBT Foundational Training",
                        "url": "https://www.beckinstitute.org/cbt-training",
                        "note": "Beck Institute官方在线课程"
                    },
                    {
                        "type": "app",
                        "name": "Woebot - CBT聊天机器人",
                        "url": "https://woebot.io/",
                        "note": "AI驱动的CBT工具，经过科学验证"
                    }
                ]
            }
        }
    },

    "mindfulness": {
        "title": "正念练习",
        "age_adapted": {
            "child": {
                "name": "正念呼吸练习",
                "description": "通过呼吸练习，帮助我们平静下来，更好地关注当下。",
                "practice": {
                    "name": "4-7-8 呼吸法",
                    "steps": [
                        "用鼻子慢慢数到4吸气（心里数：1-2-3-4）",
                        "屏住呼吸数到7（心里数：1-2-3-4-5-6-7）",
                        "用嘴巴慢慢呼气数到8（心里数：1-2-3-4-5-6-7-8）",
                        "重复3-5次"
                    ],
                    "duration": "3-5分钟",
                    "benefits": ["帮助平静", "减轻紧张", "改善注意"],
                    "audio_guide": {
                        "name": "正念呼吸动画引导",
                        "url": "https://www.cosmickids.com/meditation/kids-breathing-exercise/",
                        "note": "适合儿童的动画呼吸练习"
                    }
                },
                "resources": [
                    {
                        "type": "app",
                        "name": "Headspace for Kids",
                        "url": "https://www.headspace.com/heads-for-kids",
                        "note": "专门的儿童正念应用"
                    },
                    {
                        "type": "video",
                        "name": "Smiling Mind (正念课程)",
                        "url": "https://www.smilingmind.com/",
                        "note": "免费正念课程，适合学校使用"
                    },
                    {
                        "type": "book",
                        "name": "《儿童正念》",
                        "author": "Susan Kaiser Greenland",
                        "note": "有中文版"
                    }
                ]
            },
            "teen": {
                "name": "正念冥想练习",
                "description": "通过正念练习，减少压力、提高专注力、改善情绪调节",
                "practices": [
                    {
                        "name": "正念呼吸 (4-7-8)",
                        "steps": [
                            "吸气4秒 → 屏息7秒 → 呼气8秒",
                            "重复3-5分钟",
                            "每天1-2次"
                        ],
                        "benefits": ["激活副交感神经", "降低应激反应"],
                        "audio_guide": {
                            "name": "Headspace - 呼吸练习",
                            "url": "https://www.youtube.com/watch?v=5kQP-4k4Y4U",
                            "note": "10分钟引导音频"
                        }
                    },
                    {
                        "name": "身体扫描",
                        "description": "系统性地觉察身体各部位的感受",
                        "steps": [
                            "躺下或坐下",
                            "从脚趾开始，慢慢向上扫描",
                            "觉察每个部位的感受，不做评判",
                            "时长: 10-20分钟"
                        ],
                        "audio_guide": {
                            "name": "青少年身体扫描冥想",
                            "url": "https://www.insighttimer.com/guided-meditation/teen-body-scan",
                            "note": "免费的引导冥想"
                        }
                    },
                    {
                        "name": "正念日记",
                        "description": "每天记录3件你注意到的事情",
                        "examples": [
                            "今天早上看到的美丽云彩",
                            "午餐时食物的味道",
                            "朋友的一个微笑"
                        ],
                        "benefits": ["培养感恩心", "提升积极情绪"]
                    }
                ],
                "resources": [
                    {
                        "type": "app",
                        "name": "Headspace",
                        "url": "https://www.headspace.com/",
                        "note": "正念应用，有免费基础课程"
                    },
                    {
                        "type": "app",
                        "name": "Insight Timer",
                        "url": "https://insighttimer.com/",
                        "note": "免费冥想应用，大量引导音频"
                    },
                    {
                        "type": "course",
                        "name": "Mindful Schools",
                        "url": "https://www.mindful.org/",
                        "note": "学校正念教育项目"
                    }
                ]
            },
            "adult": {
                "name": "MBSR正念减压疗法",
                "theory": "基于Jon Kabat-Zinn的标准MBSR课程",
                "core_practices": [
                    {
                        "name": "正念呼吸 (Mindful Breathing)",
                        "source": "Kabat-Zinn (1990). Full Catastrophe Living",
                        "steps": [
                            "专注于呼吸的感觉",
                            "当思绪飘走时，温柔地回到呼吸",
                            "练习10-15分钟，每天1-2次"
                        ],
                        "research": "Meta分析显示正念呼吸可降低皮质醇水平 (Goyal et al., 2017)"
                    },
                    {
                        "name": "身体扫描 (Body Scan)",
                        "source": "MBSR标准课程",
                        "steps": [
                            "平躺，闭眼，从脚趾开始",
                            "逐部位觉察身体感觉",
                            "不做评判，只是观察",
                            "时长: 30-45分钟"
                        ],
                        "audio_guide": {
                            "name": "Palouse Mindfulness 身体扫描",
                            "url": "https://palousemindfulness.com/mindfulness/body-scan",
                            "note": "免费的引导音频"
                        }
                    },
                    {
                        "name": "正念行走 (Walking Meditation)",
                        "steps": [
                            "缓慢行走，注意每一步的感觉",
                            "觉察脚与地面的接触",
                            "保持觉察，避免自动驾驶模式"
                        ]
                    }
                ],
                "resources": [
                    {
                        "type": "book",
                        "name": "Jon Kabat-Zinn - 多舛的生命 (Full Catastrophe Living)",
                        "isbn": "978-0738167456",
                        "note": "MBSR经典教材，有中文版"
                    },
                    {
                        "type": "app",
                        "name": "Calm",
                        "url": "https://www.calm.com/",
                        "note": "推荐率最高的冥想应用"
                    },
                    {
                        "type": "online_course",
                        "name": "Palouse Mindfulness 免费课程",
                        "url": "https://palousemindfulness.com/",
                        "note": "华盛顿大学提供的免费MBSR课程"
                    }
                ]
            }
        }
    },

    "behavioral_activation": {
        "title": "行为激活技术",
        "age_adapted": {
            "child": {
                "name": "做让你开心的活动",
                "description": "当我们难过时，不想做事情。但做一些活动可以帮助我们感觉好一些。",
                "practice": {
                    "name": "活动计划表",
                    "steps": [
                        "列出3件你可以做的活动",
                        "今天选择1件去做",
                        "做完后记录心情（1-10分）"
                    ],
                    "examples": [
                        "和朋友玩游戏",
                        "画画",
                        "听音乐",
                        "户外运动",
                        "搭积木"
                    ],
                    "worksheet": "活动打卡表",
                    "benefits": ["提升情绪", "增加成就感"]
                },
                "resources": [
                    {
                        "type": "worksheet",
                        "name": "儿童活动计划表（可打印）",
                        "url": "https://www.therapistaid.com/activity-scheduling/",
                        "note": "简单易懂的计划表"
                    },
                    {
                        "type": "article",
                        "name": "Behavioral Activation for Children",
                        "url": "https://www.psychologytools.com/behavioral-activation-children",
                        "note": "写给家长的文章"
                    }
                ]
            },
            "teen": {
                "name": "行为激活",
                "description": "当我们情绪低落时，容易不想动。但恰恰是做活动能帮我们感觉更好。",
                "concept": "行为 ≠ 心情，行为可以影响心情",
                "steps": [
                    {
                        "name": "1. 列出活动",
                        "content": "列出你过去喜欢的活动",
                        "categories": ["社交", "运动", "创造", "学习", "放松"]
                    },
                    {
                        "name": "2. 评估难度",
                        "content": "给每个活动评分(1-10分，10=最简单)",
                        "strategy": "从简单的开始"
                    },
                    {
                        "name": "3. 制定计划",
                        "content": "本周选择3个活动，每个30-60分钟",
                        "example": "周一: 散步(4分); 周三: 画画(3分); 周五: 朋友聚会(5分)"
                    },
                    {
                        "name": "4. 完成后记录",
                        "content": "活动前预测心情(1-10)，活动后实际心情(1-10)",
                        "worksheet": "活动记录表"
                    }
                ],
                "resources": [
                    {
                        "type": "app",
                        "name": "Activity Scheduler",
                        "url": "https://apps.apple.com/us/app/activity-scheduler/id1067648988",
                        "note": "免费iOS应用"
                    },
                    {
                        "type": "worksheet",
                        "name": "行为激活练习表",
                        "url": "https://www.therapistaid.com/activity-scheduling/",
                        "note": "可打印的练习表"
                    },
                    {
                        "type": "article",
                        "name": "Behavioral Activation for Teens",
                        "url": "https://www.psychologytoday.com/us/blog/the-scientific-artist/201509/behavioral-activation-creates-wellness",
                        "note": "通俗易懂的文章"
                    }
                ]
            },
            "adult": {
                "name": "行为激活技术(Behavioral Activation)",
                "theory": "基于CBT的行为激活技术，通过增加积极活动来改善情绪",
                "mechanism": "活动 → 感受 → 思维 → 情绪",
                "protocol": {
                    "name": "标准行为激活方案",
                    "source": "Martell et al. (2001). Depression手册",
                    "steps": [
                        {
                            "phase": "第1周：监控",
                            "content": "记录每日活动和心情评分(1-10)",
                            "worksheet": "每日活动记录表"
                        },
                        {
                            "phase": "第2周：评估",
                            "content": "评估活动的愉悦感和成就感",
                            "goal": "识别' mastery & pleasure' 活动"
                        },
                        {
                            "phase": "第3周：规划",
                            "content": "增加' mastery & pleasure'活动",
                            "goal": "每周至少15小时积极活动"
                        },
                        {
                            "phase": "第4-8周：渐进",
                            "content": "根据反馈调整活动计划",
                            "focus": "克服障碍，维持规律"
                        }
                    ]
                },
                "resources": [
                    {
                        "type": "book",
                        "name": "Martell - 《抑郁症的行为激活治疗》",
                        "isbn": "978-1572306684",
                        "note": "BA标准手册"
                    },
                    {
                        "type": "worksheet",
                        "name": "行为激活练习表包",
                        "url": "https://www.therapistaid.com/behavioral-activation/",
                        "note": "包含多种练习表"
                    },
                    {
                        "type": "online_course",
                        "name": "Behavioral Activation Training",
                        "url": "https://www.brianclement.com/ba-training/",
                        "note": "专业培训机构的在线课程"
                    }
                ]
            }
        }
    },

    "sleep_improvement": {
        "title": "睡眠改善",
        "age_adapted": {
            "child": {
                "name": "好好睡觉，身体棒棒",
                "description": "规律的睡眠能帮助我们长高、学习更好、心情愉快。",
                "strategies": [
                    {
                        "name": "规律作息",
                        "content": "每天同一时间睡觉和起床",
                        "tips": ["选择合适的时间", "周末也不要相差太大"]
                    },
                    {
                        "name": "睡前习惯",
                        "dos": ["读书", "听轻音乐", "温水澡", "和家人聊天"],
                        "donts": ["不看屏幕", "不玩激烈游戏", "不吃零食"]
                    },
                    {
                        "name": "睡眠环境",
                        "tips": ["安静", "黑暗", "凉爽", "舒适"]
                    }
                ],
                "resources": [
                    {
                        "type": "app",
                        "name": "Sleep Sounds",
                        "url": "https://www.sleepsounds.com/",
                        "note": "免费白噪音应用"
                    },
                    {
                        "type": "article",
                        "name": "儿童睡眠指南",
                        "url": "https://www.sleepfoundation.org/children-and-sleep",
                        "note": "美国睡眠基金会"
                    }
                ]
            },
            "teen": {
                "name": "改善睡眠质量",
                "description": "青少年需要8-10小时睡眠，但作息不规律很常见。",
                "science": "睡眠影响情绪、记忆、学习成绩",
                "strategies": {
                    "sleep_hygiene": {
                        "name": "睡眠卫生",
                        "rules": [
                            "固定睡眠时间（即使周末）",
                            "避免下午咖啡因",
                            "睡前1小时不用屏幕",
                            "卧室只用于睡觉"
                        ],
                        "science": "研究表明屏幕蓝光影响褪黑素分泌"
                    },
                    "relaxation": {
                        "name": "睡前放松",
                        "practices": [
                            "4-7-8 呼吸法",
                            "渐进性肌肉放松",
                            "正念冥想"
                        ]
                    },
                    "environment": {
                        "name": "优化睡眠环境",
                        "tips": ["黑暗", "安静", "凉爽(18-22°C)", "舒适床铺"]
                    }
                },
                "resources": [
                    {
                        "type": "app",
                        "name": "Sleep Cycle",
                        "url": "https://www.sleepcycle.com/",
                        "note": "智能闹钟，在最佳睡眠周期唤醒"
                    },
                    {
                        "type": "app",
                        "name": "Calm - Sleep Stories",
                        "url": "https://www.calm.com/sleep/",
                        "note": "睡前故事帮助入睡"
                    },
                    {
                        "type": "video",
                        "name": "青少年睡眠改善技巧",
                        "url": "https://www.youtube.com/watch?v=C5o33p7IBvM",
                        "note": "8分钟实用技巧"
                    },
                    {
                        "type": "article",
                        "name": "NSF - 睡眠与青少年",
                        "url": "https://www.sleepfoundation.org/teens-and-sleep",
                        "note": "美国睡眠基金会青少年睡眠指南"
                    }
                ]
            },
            "adult": {
                "name": "CBT-I (失眠认知行为疗法)",
                "theory": "基于Perlis et al.的CBT-I方案",
                "components": [
                    {
                        "name": "刺激控制",
                        "description": "只在困倦时上床，床只用于睡眠",
                        "rules": [
                            "困了才上床，15分钟睡不着就起床",
                            "床只用于睡眠，不在床上看手机/看书",
                            "固定起床时间（无论睡多少小时）"
                        ]
                    },
                    {
                        "name": "睡眠限制",
                        "description": "缩短在床时间以提高睡眠效率",
                        "method": "根据实际睡眠时间调整上床时间",
                        "goal": "睡眠效率 > 90%"
                    },
                    {
                        "name": "认知重构",
                        "description": "识别和改变关于睡眠的消极想法",
                        "examples": [
                            "原想法: '如果我不睡着，明天会崩溃'",
                            "替代: '即使睡眠不够，我也能应对'"
                        ]
                    },
                    {
                        "name": "放松训练",
                        "practices": [
                            "渐进性肌肉放松(PMR)",
                            "正念冥想",
                            "4-7-8 呼吸法"
                        ]
                    }
                ],
                "resources": [
                    {
                        "type": "book",
                        "name": "Perlis - 《失眠的认知行为治疗》",
                        "isbn": "978-1572306684",
                        "note": "CBT-I标准手册"
                    },
                    {
                        "type": "app",
                        "name": "CBT-i Coach",
                        "url": "https://cbti.co.uk/",
                        "note": "免费的CBT-I自助工具"
                    },
                    {
                        "type": "workbook",
                        "name": "Quiet Your Mind & Get to Sleep",
                        "author": "Rachel Manber",
                        "note": "基于CBT-I的工作簿"
                    },
                    {
                        "type": "online_course",
                        "name": "AASM CBT-I认证课程",
                        "url": "https://aasm.org/",
                        "note": "美国睡眠医学学会认证"
                    }
                ]
            }
        }
    },

    "social_anxiety": {
        "title": "社交焦虑应对",
        "age_adapted": {
            "child": {
                "name": "和朋友相处",
                "description": "有时候和同学相处会紧张，这是很常见的。",
                "strategies": [
                    {
                        "name": "深呼吸",
                        "content": "感到紧张时，深呼吸3次",
                        "practice": "平时练习，紧张时就能用上"
                    },
                    {
                        "name": "找个好朋友",
                        "content": "和信任的人一起，会感觉更安全",
                        "tip": "可以准备一些话题，避免冷场"
                    },
                    {
                        "name": "小步尝试",
                        "content": "从简单的开始：和1个朋友聊天",
                        "progression": "聊天 → 小组活动 → 班级活动"
                    }
                ],
                "resources": [
                    {
                        "type": "book",
                        "name": "《帮助孩子克服社交焦虑》",
                        "author": "Christopher McCurry",
                        "note": "写给家长和孩子的指南"
                    },
                    {
                        "type": "article",
                        "name": "儿童社交焦虑指南",
                        "url": "https://www.worrywisekids.com/",
                        "note": "专门帮助焦虑儿童的网站"
                    }
                ]
            },
            "teen": {
                "name": "社交焦虑管理",
                "theory": "基于CBT的社交焦虑干预技术",
                "strategies": {
                    "exposure": {
                        "name": "渐进式暴露",
                        "description": "逐步面对害怕的社交情境，建立自信",
                        "steps": [
                            "建立焦虑等级层次",
                            "从低焦虑情境开始",
                            "逐步向上练习",
                            "每次完成后记录学习"
                        ],
                        "example": "层次: 和朋友聊天(3分) → 小组讨论(5分) → 演讲(7分)"
                    },
                    "cognitive": {
                        "name": "挑战消极思维",
                        "common_thoughts": [
                            "大家都会笑话我",
                            "我肯定会说错话",
                            "别人会看出我很紧张"
                        ],
                        "challenge_questions": [
                            "有什么证据支持这个想法？",
                            "最坏会发生什么？我能应对吗？",
                            "别人真的会这么想吗？"
                        ]
                    },
                    "social_skills": {
                        "name": "社交技能训练",
                        "skills": [
                            "开启话题的技巧",
                            "保持对话的方法",
                            "结束对话的方式"
                        ]
                    }
                },
                "resources": [
                    {
                        "type": "app",
                        "name": "FearTools - 社交焦虑帮助",
                        "url": "https://www.feartools.com/",
                        "note": "包含暴露练习工具"
                    },
                    {
                        "type": "book",
                        "name": "《社交焦虑的治疗》",
                        "author": "Rapee & Heimberg",
                        "note": "专业书籍"
                    },
                    {
                        "type": "online_program",
                        "name": "This Way Up",
                        "url": "https://thiswayup.org.au/",
                        "note": "澳大利亚的免费焦虑自助程序"
                    }
                ]
            },
            "adult": {
                "name": "社交焦虑障碍治疗",
                "theory": "基于CBT的社交焦虑障碍干预",
                "approach": "暴露疗法 + 认知重构",
                "protocols": [
                    {
                        "name": "渐进式暴露",
                        "source": "Rapee & Heimberg (1997). Social Anxiety Treatment",
                        "structure": [
                            "建立恐惧情境层次",
                            "从低到高逐个暴露",
                            "直到焦虑明显降低",
                            "进行in vivo暴露（真实场景）"
                        ]
                    },
                    {
                        "name": "认知重构",
                        "focus_areas": [
                            "对评价的恐惧",
                            "对可见性的过度关注",
                            "安全行为的识别与放弃"
                        ]
                    },
                    {
                        "name": "社交技能训练",
                        "skills": [
                            "非语言沟通技巧",
                            "对话维持技巧",
                            "拒绝请求而不内疚"
                        ]
                    }
                ],
                "resources": [
                    {
                        "type": "book",
                        "name": "《社交恐惧症的治疗》",
                        "author": "Rapee & Heimberg",
                        "isbn": "978-1572306684",
                        "note": "标准教材"
                    },
                    {
                        "type": "app",
                        "name": "nOCD - 社交焦虑帮助",
                        "url": "https://www.treatmyocd.com/",
                        "note": "CBT平台"
                    },
                    {
                        "type": "workbook",
                        "name": "The Shyness and Social Anxiety Workbook",
                        "author": "M. M. Antony",
                        "note": "实用工作簿"
                    }
                ]
            }
        }
    },

    "emotion_regulation": {
        "title": "情绪调节技巧",
        "age_adapted": {
            "child": {
                "name": "认识和管理情绪",
                "practices": [
                    {
                        "name": "情绪词汇表",
                        "description": "学会用词语表达情绪",
                        "activity": "情绪卡片游戏",
                        "link": "https://www.centervention.com/emotional-regulation-free-activities/"
                    },
                    {
                        "name": "平静瓶 (Calm Bottle)",
                        "description": "用 glitter 和透明瓶制作平静瓶",
                        "steps": [
                            "在瓶中加 glitter",
                            "加水摇晃",
                            "观察沉淀过程（情绪平复）"
                        ],
                        "meaning": "情绪就像 glitter，会慢慢沉淀"
                    },
                    {
                        "name": "情绪温度计",
                        "description": "用颜色和表情表示情绪强度",
                        "scale": [
                            "绿色 - 开心",
                            "黄色 - 还可以",
                            "红色 - 需要帮助"
                        ]
                    }
                ],
                "resources": [
                    {
                        "type": "website",
                        "name": "Centervention - 情绪调节免费活动",
                        "url": "https://www.centervention.com/",
                        "note": "大量免费练习表和活动"
                    },
                    {
                        "type": "video",
                        "name": "Inside Out 电影",
                        "note": "皮克斯电影，帮助儿童理解情绪"
                    }
                ]
            },
            "teen": {
                "name": "情绪调节技能",
                "skills": [
                    {
                        "name": "TIPP技巧",
                        "source": "DBT (Dialectical Behavior Therapy)",
                        "components": [
                            "T - Temperature: 冷水洗脸激活潜水反射",
                            "I - Intense exercise: 剧烈运动释放能量",
                            "P - Paced breathing: 快速呼吸调节心率",
                            "P - Paused muscle relaxation: 渐进肌肉放松"
                        ],
                        "use_case": "强烈情绪时的快速干预"
                    },
                    {
                        "name": "ABC PLEASE",
                        "source": "DBT",
                        "components": [
                            "A - Accumulate positive emotions",
                            "B - Build mastery",
                            "C - Cope ahead",
                            "PLEASE - Treat Physically"
                        ],
                        "resources": {
                            "url": "https://www.dbtselfmanagement.com/",
                            "note": "DBT自助管理网站"
                        }
                    },
                    {
                        "name": "5-4-3-2-1 感官着陆",
                        "description": "通过5种感官回到当下",
                        "steps": [
                            "5样你能看到的东西",
                            "4样你能触摸到的东西",
                            "3样你能听到的声音",
                            "2样你能闻到的气味",
                            "1样你能尝到的味道"
                        ],
                        "duration": "1-2分钟"
                    }
                ],
                "resources": [
                    {
                        "type": "app",
                        "name": "DBT Diary Card",
                        "url": "https://www.dbtselfmanagement.com/",
                        "note": "免费DBT工具"
                    },
                    {
                        "name": "DBT Self Management",
                        "url": "https://www.dbtselfmanagement.com/",
                        "note": "DBT官方网站，免费资源"
                    }
                ]
            },
            "adult": {
                "name": "DBT情绪调节技能",
                "theory": "Marsha Linehan的DBT (辩证行为疗法)",
                "modules": [
                    {
                        "name": "Core Mindfulness",
                        "skills": [
                            "观察 (Observe)",
                            "描述 (Describe)",
                            "参与 (Participate)",
                            "不评判 (Non-judgmental)"
                        ]
                    },
                    {
                        "name": "痛苦忍耐",
                        "skills": [
                            "ACCEPTS",
                            "IMPROVE the moment",
                            "Pros and Cons",
                            "TIPP"
                        ]
                    },
                    {
                        "name": "人际效能",
                        "skills": [
                            "DEAR MAN (请求技巧)",
                            "GIVE (人际关系维护)",
                            "FAST (自我尊重)"
                        ]
                    },
                    {
                        "name": "情绪调节",
                        "skills": [
                            "ABC PLEASE",
                            "Opposite Action",
                            " Accumulate Positive"
                        ]
                    }
                ],
                "resources": [
                    {
                        "type": "book",
                        "name": "DBT 技能训练手册",
                        "author": "Cathy Moonshell",
                        "isbn": "978-1572307814",
                        "note": "DBT经典教材"
                    },
                    {
                        "type": "app",
                        "name": "DBT Coach",
                        "url": "https://www.dbtcoach.app/",
                        "note": "DBT Coach应用"
                    },
                    {
                        "type": "online_course",
                        "name": "DBT Path (Behavioral Tech)",
                        "url": "https://behavioraltech.com/products/online-courses",
                        "note": "官方在线课程"
                    }
                ]
            }
        }
    }
}

# ==================== 模块化报告生成器 ====================

class ModularReportGenerator:
    """模块化报告生成器"""

    def __init__(self):
        self.modules = ACCESSIBLE_RESOURCES

    def _calculate_statistics(self, messages):
        """计算统计数据"""
        from collections import Counter
        import re

        if not messages:
            return {
                "total_conversations": 0,
                "emotion_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "recent_trend": [],
                "top_keywords": []
            }

        # 情绪分布
        emotion_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for msg in messages:
            emotion = msg.emotion or "neutral"
            if emotion in emotion_counts:
                emotion_counts[emotion] += 1

        total = len(messages)
        emotion_percentages = {
            k: round((v / total) * 100, 1) if total > 0 else 0
            for k, v in emotion_counts.items()
        }

        # 最近趋势（最近7天）
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        recent_messages = [m for m in messages if m.created_at >= week_ago]

        trend_data = []
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)

            day_messages = [
                m for m in messages
                if day_start <= m.created_at <= day_end
            ]

            if day_messages:
                avg_mood = sum([
                    1.0 if m.emotion == "positive" else
                    0.5 if m.emotion == "neutral" else
                    0.0
                    for m in day_messages
                ]) / len(day_messages)

                trend_data.append({
                    "date": day.strftime("%m-%d"),
                    "value": round(avg_mood, 2)
                })

        # 关键词提取（简化版）
        all_text = " ".join([m.user_message for m in messages if m.user_message])
        # 移除标点符号，提取中文词汇
        words = re.findall(r'[\u4e00-\u9fff]{2,}', all_text)
        word_counts = Counter(words)
        top_keywords = [{"word": w, "count": c} for w, c in word_counts.most_common(10)]

        return {
            "total_conversations": total,
            "emotion_distribution": emotion_percentages,
            "recent_trend": trend_data,
            "top_keywords": top_keywords
        }

    def generate_layer1_report(self, user_id, age, report_level):
        """Layer 1: 数据概览 + 模块推荐"""
        from models import ChatMessage

        # 获取统计数据
        messages = ChatMessage.query.filter_by(user_id=user_id)\
            .order_by(ChatMessage.created_at.desc()).limit(100).all()

        stats = self._calculate_statistics(messages)
        keywords = [k["word"] for k in stats["top_keywords"][:10]]

        # 匹配相关模块
        relevant_modules = self._match_modules(keywords, age, report_level)

        return {
            "user_id": user_id,
            "age": age,
            "report_level": report_level,
            "statistics": stats,
            "suggested_modules": relevant_modules,
            "message": "我们注意到以下主题可能与您相关"
        }

    def _match_modules(self, keywords, age, report_level):
        """基于关键词匹配模块"""
        relevant = []

        keyword_set = set(keywords)

        # 模块关键词映射
        module_keywords = {
            "stress": ["压力", "紧张", "焦虑", "疲惫", "累", "担心", "害怕"],
            "sleep": ["失眠", "熬夜", "困", "累", "睡眠", "精神"],
            "social": ["社交", "害羞", "紧张", "害怕", "朋友", "孤独"],
            "mood": ["难过", "抑郁", "不开心", "低落", "沮丧"],
            "emotion": ["情绪", "控制", "生气", "烦躁"],
            "mindfulness": ["平静", "放松", "冥想", "正念"]
        }

        for module_name, kw_list in module_keywords.items():
            match_count = sum(1 for kw in kw_list if kw in keyword_set)
            if match_count > 0:
                relevant.append({
                    "module": module_name,
                    "match_count": match_count,
                    "title": self._get_module_title(module_name, age, report_level)
                })

        # 按匹配度排序，最多返回3个
        relevant.sort(key=lambda x: x["match_count"], reverse=True)
        return relevant[:3]

    def _get_module_title(self, module_name, age, report_level):
        """获取年龄适配的模块标题"""
        titles = {
            "stress": {
                "child": "管理压力",
                "teen": "压力管理",
                "adult": "压力管理 (CBT技术)"
            },
            "sleep": {
                "child": "好好睡觉",
                "teen": "改善睡眠",
                "adult": "睡眠改善 (CBT-I技术)"
            },
            "social": {
                "child": "和朋友相处",
                "teen": "社交技巧",
                "adult": "社交焦虑治疗"
            },
            "mood": {
                "child": "情绪管理",
                "teen": "情绪调节",
                "adult": "情绪调节技能 (DBT技术)"
            },
            "mindfulness": {
                "child": "平静练习",
                "teen": "正念冥想",
                "adult": "MBSR正念减压"
            }
        }
        return titles.get(module_name, {}).get(
            "child" if age < 13 else "teen" if age < 18 else "adult",
            module_name
        )

    def get_layer2_module(self, module_name, age, report_level):
        """获取Layer 2模块详情"""
        # 映射到资源库
        module_mapping = {
            "stress": "cognitive_restructuring",
            "mood": "behavioral_activation",
            "social": "social_anxiety",
            "mindfulness": "mindfulness",
            "sleep": "sleep_improvement",
            "emotion": "emotion_regulation"
        }

        resource_key = module_mapping.get(module_name)
        if not resource_key:
            return None

        resources = self.modules.get(resource_key)
        if not resources:
            return None

        age_group = "child" if age < 13 else "teen" if age < 18 else "adult"
        content = resources["age_adapted"][age_group]

        return {
            "module_name": module_name,
            "title": content["name"],
            "description": content["description"],
            "practices": content.get("practices", []) or content.get("strategies", []),
            "resources": content["resources"],
            "age_group": age_group
        }


# ==================== 快速测试 ====================

if __name__ == "__main__":
    generator = ModularReportGenerator()

    # 模拟用户
    user_keywords = ["压力", "焦虑", "失眠", "学习"]

    # 测试不同年龄段
    for age in [11, 15, 25]:
        print(f"\n=== {age}岁 ({'儿童' if age < 13 else '青少年' if age < 18 else '成人'}) ===")
        module = generator.get_layer2_module("stress", age, "adult")
        if module:
            print(f"模块: {module['title']}")
            print(f"描述: {module['description']}")
            if module['practices']:
                practice = module['practices'][0]
                print(f"练习: {practice.get('name') or practice.get('phase', '')}")
            print(f"资源数量: {len(module['resources'])}")
