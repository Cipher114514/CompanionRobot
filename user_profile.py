# -*- coding: utf-8 -*-
"""
用户画像系统 - 完整重构版
支持持续学习、智能提取和数据库持久化
"""

import re
import json
from typing import Dict, Optional, List, Tuple
from datetime import datetime


class UserProfile:
    """用户画像管理类 - 支持持续学习和智能提取"""

    # 扩展的关键词模式
    PATTERNS = {
        'name': [
            r'我叫(\w{1,4})',
            r'我是(\w{1,4})',
            r'名字叫(\w{1,4})',
            r'叫我(\w{1,4})',
            r'我是([a-zA-Z]{1,10})'  # 英文名
        ],
        'age': [
            r'(\d+)岁',
            r'年龄(\d+)',
            r'(\d+)周岁',
            r'今年(\d+)岁'
        ],
        'job': {
            '程序员': ['程序员', '软件工程师', '开发工程师', '前端', '后端', '全栈', '码农', '开发者'],
            '医生': ['医生', '医师', '护士', '医护人员'],
            '老师': ['老师', '教师', '教授', '讲师', '辅导员'],
            '学生': ['学生', '大学生', '研究生', '博士生', '中学生', '高中生'],
            '设计师': ['设计师', 'UI设计师', 'UX设计师', '平面设计'],
            '产品经理': ['产品经理', 'PM', '产品'],
            '销售': ['销售', '销售员', '业务员'],
            '会计': ['会计', '财务', '出纳'],
            '律师': ['律师', '法务'],
            '公务员': ['公务员', '体制内', '事业单位'],
            '自由职业': ['自由职业', '自媒体', '个体户'],
            '其他': ['工作', '上班', '职业']
        },
        'hobbies': {
            '运动': ['打篮球', '篮球', '跑步', '健身', '游泳', '瑜伽', '羽毛球', '乒乓球', '足球', '网球', '爬山', '骑行'],
            '音乐': ['唱歌', '听歌', '音乐', '吉他', '钢琴', '弹琴', '演奏'],
            '阅读': ['看书', '阅读', '读书', '小说', '文学'],
            '游戏': ['游戏', '打游戏', '玩游戏', '电子游戏', '王者荣耀', '英雄联盟'],
            '影视': ['看电影', '看剧', '电视剧', '电影', '动漫', '追剧'],
            '旅行': ['旅行', '旅游', '出游', '游玩'],
            '美食': ['美食', '做饭', '烹饪', '烘焙', '吃', '美食探店'],
            '摄影': ['摄影', '拍照', '拍照'],
            '绘画': ['画画', '绘画', '画', '素描'],
            '宠物': ['宠物', '猫', '狗', '养猫', '养狗']
        },
        'concerns': {
            '睡眠问题': ['失眠', '睡不着', '睡眠不好', '多梦', '早醒', '睡眠障碍'],
            '工作压力': ['工作压力', '工作累', '工作忙', '加班', '职场压力', '工作烦恼'],
            '学习压力': ['学习压力', '考试', '学业', '学习困难', '学习焦虑'],
            '情绪问题': ['焦虑', '抑郁', '情绪低落', '情绪不稳定', '情绪化'],
            '人际关系': ['人际关系', '社交', '朋友', '同事', '孤独', '孤单'],
            '家庭问题': ['家庭', '父母', '孩子', '家务', '家庭矛盾'],
            '健康问题': ['健康', '身体不舒服', '生病', '身体不好'],
            '经济压力': ['经济压力', '钱', '财务', '债务', '经济困难']
        }
    }

    def __init__(self, user=None):
        """
        初始化用户画像

        Args:
            user: SQLAlchemy User 对象（可选）
        """
        self.user = user
        if user:
            self.profile = user.get_profile_data()
        else:
            self.profile = {
                'name': None,
                'age': None,
                'job': None,
                'hobbies': [],
                'concerns': [],
                'preferences': {},
                'last_updated': None,
                # 新增：置信度和元数据
                'confidence': {
                    'name': 0.0,
                    'age': 0.0,
                    'job': 0.0,
                    'hobbies': {},  # {hobby: confidence}
                    'concerns': {}  # {concern: confidence}
                },
                'metadata': {
                    'total_messages_analyzed': 0,
                    'extraction_sources': []  # 记录信息来源
                }
            }

        # 常量配置
        self.MAX_HOBBIES = 20  # 最大爱好数量
        self.MAX_CONCERNS = 20  # 最大困扰数量
        self.MIN_CONFIDENCE = 0.3  # 最低置信度阈值

    def extract_from_message(self, message: str) -> Tuple[bool, List[str]]:
        """
        从消息中提取用户信息（持续学习）
        - 增加置信度计算
        - 限制列表字段数量
        - 优化提取准确性

        Args:
            message: 用户消息

        Returns:
            (是否更新, 更新的字段列表)
        """
        if not message:
            return False, []

        updated = False
        updated_fields = []

        # 初始化confidence和metadata字段（兼容旧数据）
        if 'confidence' not in self.profile:
            self.profile['confidence'] = {
                'age': 0.0,
                'job': 0.0,
                'hobbies': {},
                'concerns': {}
            }
        if 'metadata' not in self.profile:
            self.profile['metadata'] = {
                'total_messages_analyzed': 0,
                'extraction_sources': []
            }

        # 更新消息计数
        self.profile['metadata']['total_messages_analyzed'] += 1

        # 1. 姓名提取已禁用（陪伴过程中姓名不重要）
        # if not self.profile['name']:
        #     name, confidence = self._extract_name_with_confidence(message)
        #     if name and confidence >= self.MIN_CONFIDENCE:
        #         self.profile['name'] = name
        #         self.profile['confidence']['name'] = confidence
        #         updated = True
        #         updated_fields.append('name')
        #         print(f"[用户画像] 提取名字: {name} (置信度: {confidence:.2f})")

        # 2. 提取年龄（仅首次，带置信度）
        if not self.profile['age']:
            age, confidence = self._extract_age_with_confidence(message)
            if age and confidence >= self.MIN_CONFIDENCE:
                self.profile['age'] = age
                self.profile['confidence']['age'] = confidence
                updated = True
                updated_fields.append('age')
                print(f"[用户画像] 提取年龄: {age} (置信度: {confidence:.2f})")

        # 3. 提取职业（可更新，带置信度）
        job, confidence = self._extract_job_with_confidence(message)
        if job and confidence >= self.MIN_CONFIDENCE:
            # 只在置信度更高时才更新（避免低置信度覆盖高置信度）
            if confidence > self.profile['confidence']['job']:
                self.profile['job'] = job
                self.profile['confidence']['job'] = confidence
                updated = True
                updated_fields.append('job')
                print(f"[用户画像] 提取职业: {job} (置信度: {confidence:.2f})")

        # 4. 提取爱好（累加，带数量限制和置信度）
        new_hobbies = self._extract_hobbies_with_confidence(message)
        if new_hobbies:
            for hobby, confidence in new_hobbies.items():
                # 检查是否已存在（追踪提及频率）
                if hobby in self.profile['hobbies']:
                    # 获取之前的提及次数
                    mention_count = self.profile['confidence']['hobbies'].get(f'{hobby}_count', 0) + 1
                    self.profile['confidence']['hobbies'][f'{hobby}_count'] = mention_count

                    # 基于频率的置信度提升（最多提升到1.0）
                    frequency_boost = min(mention_count * 0.1, 0.3)

                    # 更新置信度：取原置信度、新置信度、频率提升的最大值
                    old_confidence = self.profile['confidence']['hobbies'].get(hobby, 0)
                    new_confidence_with_boost = min(confidence + frequency_boost, 1.0)
                    final_confidence = max(old_confidence, new_confidence_with_boost)

                    if final_confidence != old_confidence:
                        self.profile['confidence']['hobbies'][hobby] = final_confidence
                else:
                    # 检查数量限制
                    if len(self.profile['hobbies']) < self.MAX_HOBBIES:
                        if confidence >= self.MIN_CONFIDENCE:
                            self.profile['hobbies'].append(hobby)
                            self.profile['confidence']['hobbies'][hobby] = confidence
                            self.profile['confidence']['hobbies'][f'{hobby}_count'] = 1  # 初始化提及次数
                            updated = True
                            updated_fields.append('hobbies')
                            print(f"[用户画像] 新增爱好: {hobby} (置信度: {confidence:.2f}, 总数: {len(self.profile['hobbies'])})")
                    else:
                        print(f"[用户画像] 爱好数量已达上限 ({self.MAX_HOBBIES})，跳过: {hobby}")

        # 5. 提取困扰（累加，带数量限制和置信度）
        new_concerns = self._extract_concerns_with_confidence(message)
        if new_concerns:
            for concern, confidence in new_concerns.items():
                # 检查是否已存在（追踪提及频率）
                if concern in self.profile['concerns']:
                    # 获取之前的提及次数
                    mention_count = self.profile['confidence']['concerns'].get(f'{concern}_count', 0) + 1
                    self.profile['confidence']['concerns'][f'{concern}_count'] = mention_count

                    # 基于频率的置信度提升（困扰提及越多越重要）
                    frequency_boost = min(mention_count * 0.15, 0.4)

                    # 更新置信度
                    old_confidence = self.profile['confidence']['concerns'].get(concern, 0)
                    new_confidence_with_boost = min(confidence + frequency_boost, 1.0)
                    final_confidence = max(old_confidence, new_confidence_with_boost)

                    if final_confidence != old_confidence:
                        self.profile['confidence']['concerns'][concern] = final_confidence
                else:
                    # 检查数量限制
                    if len(self.profile['concerns']) < self.MAX_CONCERNS:
                        if confidence >= self.MIN_CONFIDENCE:
                            self.profile['concerns'].append(concern)
                            self.profile['confidence']['concerns'][concern] = confidence
                            self.profile['confidence']['concerns'][f'{concern}_count'] = 1  # 初始化提及次数
                            updated = True
                            updated_fields.append('concerns')
                            print(f"[用户画像] 新增困扰: {concern} (置信度: {confidence:.2f}, 总数: {len(self.profile['concerns'])})")
                    else:
                        print(f"[用户画像] 困扰数量已达上限 ({self.MAX_CONCERNS})，跳过: {concern}")

        # 6. 提取对话偏好
        prefs = self._extract_preferences(message)
        if prefs:
            self.profile['preferences'].update(prefs)
            updated = True
            updated_fields.append('preferences')

        # 更新时间戳
        if updated:
            self.profile['last_updated'] = datetime.utcnow().isoformat()

        return updated, updated_fields

    def _extract_name(self, message: str) -> Optional[str]:
        """提取名字（旧方法，保持兼容）"""
        result, _ = self._extract_name_with_confidence(message)
        return result

    def _calculate_confidence(self, base: float, factors: dict) -> float:
        """
        计算综合置信度（科学的多因子加权模型）

        Args:
            base: 基础置信度
            factors: 影响因子字典
                - expression_strength: 表达强度 (0.0-1.0)
                - first_person: 第一人称肯定 (True/False)
                - specificity: 关键词特异性 (0.0-1.0)
                - historical_consistency: 历史一致性 (0.0-1.0)
                - mention_frequency: 提及频率 (0.0-1.0)

        Returns:
            综合置信度 (0.0-1.0)
        """
        # 基础权重
        weights = {
            'base': 0.3,  # 基础置信度权重
            'expression': 0.25,  # 表达强度权重
            'first_person': 0.15,  # 第一人称权重
            'specificity': 0.1,  # 特异性权重
            'consistency': 0.15,  # 历史一致性权重
            'frequency': 0.05  # 频率权重
        }

        # 计算加权得分
        score = base * weights['base']

        if 'expression_strength' in factors:
            score += factors['expression_strength'] * weights['expression']

        if factors.get('first_person', False):
            score += weights['first_person']

        if 'specificity' in factors:
            score += factors['specificity'] * weights['specificity']

        if 'historical_consistency' in factors:
            score += factors['historical_consistency'] * weights['consistency']

        if 'mention_frequency' in factors:
            score += factors['mention_frequency'] * weights['frequency']

        return min(score, 1.0)

    def _extract_name_with_confidence(self, message: str) -> Tuple[Optional[str], float]:
        """
        提取名字（带置信度）- 改进版
        """
        # 排除模式：表示这些话不是在说自己
        exclude_patterns = [
            r'我朋友.*叫',
            r'我家人.*叫',
            r'我同事.*叫',
            r'别人.*叫',
            r'他.*叫',
            r'她.*叫',
            r'我是在.*的',
            r'我是在.*家',
            r'我是.*(地|方|处)',
            r'我是.*(推荐|介绍|告诉)',
            r'我这人',
            r'我是.*人',
            r'我是.*样',
        ]

        # 检查是否在排除模式中
        for pattern in exclude_patterns:
            if re.search(pattern, message):
                return None, 0.0

        for pattern in self.PATTERNS['name']:
            match = re.search(pattern, message)
            if match:
                name = match.group(1).strip()

                # 验证名字有效性
                invalid_names = ['在', '是', '的', '有', '不', '人', '个', '来', '去', '到', '想', '做', '说',
                                '朋友', '同事', '家人', '老师', '医生', '推荐', '介绍',
                                '这样', '那样', '这种', '那种', '怎样', '如何', '什么',
                                '这人', '某人', '谁', '谁人']
                if not name or len(name) < 2 or len(name) > 10:
                    continue
                if any(c in name for c in '0123456789=!@#$%^&*()'):
                    continue
                if name in invalid_names or any(bad in name for bad in ['人', '样', '这', '那']):
                    continue

                # 收集置信度因子
                factors = {}

                # 表达强度
                if '我叫' in message or '名字叫' in message:
                    factors['expression_strength'] = 0.9  # 明确表达
                elif '我是' in message:
                    factors['expression_strength'] = 0.4  # 较弱表达
                else:
                    factors['expression_strength'] = 0.5

                # 第一人称肯定
                factors['first_person'] = ('我' in message[:20])

                # 关键词特异性
                if len(name) >= 3:
                    factors['specificity'] = 0.8  # 名字较长，更可能是真名
                else:
                    factors['specificity'] = 0.5

                # 计算综合置信度
                confidence = self._calculate_confidence(0.5, factors)

                # 最低阈值：低于0.4不提取
                if confidence < 0.4:
                    continue

                return name, confidence
        return None, 0.0

    def _extract_age(self, message: str) -> Optional[int]:
        """提取年龄（旧方法，保持兼容）"""
        result, _ = self._extract_age_with_confidence(message)
        return result

    def _extract_age_with_confidence(self, message: str) -> Tuple[Optional[int], float]:
        """
        提取年龄（带置信度）
        改进：增加上下文验证
        """
        # 排除模式
        exclude_patterns = [
            r'我朋友.*\d+岁',
            r'我家人.*\d+岁',
            r'他.*\d+岁',
            r'她.*\d+岁'
        ]

        # 检查是否在排除模式中
        for pattern in exclude_patterns:
            if re.search(pattern, message):
                return None, 0.0

        for pattern in self.PATTERNS['age']:
            match = re.search(pattern, message)
            if match:
                try:
                    age = int(match.group(1))
                    if 5 <= age <= 100:  # 合理年龄范围
                        # 收集置信度因子
                        factors = {}

                        # 表达强度
                        if '今年' in message or '周岁' in message:
                            factors['expression_strength'] = 0.9
                        elif '岁' in message:
                            factors['expression_strength'] = 0.6
                        else:
                            factors['expression_strength'] = 0.4

                        # 第一人称肯定
                        factors['first_person'] = ('我' in message[:20])

                        # 特异性（精确数字）
                        factors['specificity'] = 0.8

                        # 计算综合置信度
                        confidence = self._calculate_confidence(0.6, factors)
                        return age, confidence
                except ValueError:
                    continue
        return None, 0.0

    def _extract_job(self, message: str) -> Optional[str]:
        """提取职业（旧方法，保持兼容）"""
        result, _ = self._extract_job_with_confidence(message)
        return result

    def _extract_job_with_confidence(self, message: str) -> Tuple[Optional[str], float]:
        """
        提取职业（带置信度）- 改进版
        增加历史一致性验证
        """
        # 排除模式
        exclude_patterns = [
            r'我朋友.*是',
            r'我家人.*是',
            r'我同事.*是',
            r'别人.*是',
            r'他.*是',
            r'她.*是',
            r'想成为',
            r'希望.*是'
        ]

        for pattern in exclude_patterns:
            if re.search(pattern, message):
                return None, 0.0

        best_job = None
        best_confidence = 0.0

        for job, keywords in self.PATTERNS['job'].items():
            for keyword in keywords:
                if keyword in message:
                    # 收集置信度因子
                    factors = {}

                    # 表达强度
                    if '我是' in message or '我的工作' in message:
                        factors['expression_strength'] = 0.8
                    elif '做' in message or '担任' in message:
                        factors['expression_strength'] = 0.6
                    else:
                        factors['expression_strength'] = 0.4

                    # 第一人称肯定
                    factors['first_person'] = ('我' in message[:30])

                    # 关键词特异性（长度 >= 3）
                    factors['specificity'] = min(len(keyword) / 5.0, 1.0)

                    # 历史一致性检查（如果之前有职业记录）
                    if self.profile.get('job'):
                        if self.profile['job'] == job:
                            # 与历史一致，提高置信度
                            factors['historical_consistency'] = 1.0
                        else:
                            # 与历史冲突，降低置信度
                            factors['historical_consistency'] = 0.3
                    else:
                        # 无历史记录，中性
                        factors['historical_consistency'] = 0.5

                    # 计算综合置信度
                    confidence = self._calculate_confidence(0.4, factors)

                    if confidence > best_confidence:
                        best_job = job
                        best_confidence = confidence

        return best_job, min(best_confidence, 1.0)

    def _extract_hobbies(self, message: str) -> List[str]:
        """提取爱好列表（旧方法，保持兼容）"""
        result_dict = self._extract_hobbies_with_confidence(message)
        return list(result_dict.keys())

    def _extract_hobbies_with_confidence(self, message: str) -> Dict[str, float]:
        """
        提取爱好列表（带置信度）- 改进版
        使用类别名称而非关键词，避免重复
        同时在metadata中保存匹配到的具体关键词
        """
        found_hobbies = {}

        # 排除模式
        exclude_patterns = [
            r'我朋友.*喜欢',
            r'我家人.*喜欢',
            r'他.*喜欢',
            r'她.*喜欢'
        ]

        for pattern in exclude_patterns:
            if re.search(pattern, message):
                return found_hobbies

        # 积极表达关键词
        positive_keywords = ['我喜欢', '我爱', '我经常', '我习惯', '我的爱好', '打打', '去游泳']

        # 初始化matched_keywords存储
        if 'matched_keywords' not in self.profile['metadata']:
            self.profile['metadata']['matched_keywords'] = {'hobbies': {}, 'concerns': {}}

        for category, keywords in self.PATTERNS['hobbies'].items():
            # 检查该类别下是否有任何关键词匹配
            best_confidence = 0.0
            best_keyword = ''
            matched_keywords_list = []

            for keyword in keywords:
                if keyword in message:
                    matched_keywords_list.append(keyword)

                    # 收集置信度因子
                    factors = {}

                    # 表达强度（优先匹配更长的关键词）
                    if any(pk in message for pk in positive_keywords):
                        factors['expression_strength'] = 0.8
                    else:
                        factors['expression_strength'] = 0.4

                    # 第一人称肯定
                    factors['first_person'] = ('我' in message[:30])

                    # 关键词特异性（更长的关键词特异性更高）
                    factors['specificity'] = min(len(keyword) / 4.0, 1.0)

                    # 计算综合置信度
                    confidence = self._calculate_confidence(0.3, factors)

                    # 保留该类别中最高的置信度
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_keyword = keyword

            # 如果该类别有关键词匹配，使用类别名称
            if best_keyword:
                found_hobbies[category] = best_confidence
                # 保存匹配到的具体关键词
                self.profile['metadata']['matched_keywords']['hobbies'][category] = matched_keywords_list

        return found_hobbies

    def _extract_concerns(self, message: str) -> List[str]:
        """提取困扰列表（旧方法，保持兼容）"""
        result_dict = self._extract_concerns_with_confidence(message)
        return list(result_dict.keys())

    def _extract_concerns_with_confidence(self, message: str) -> Dict[str, float]:
        """
        提取困扰列表（带置信度）- 改进版
        """
        found_concerns = {}

        # 排除模式
        exclude_patterns = [
            r'我朋友.*感到',
            r'我家人.*感到',
            r'他.*感到',
            r'她.*感到'
        ]

        for pattern in exclude_patterns:
            if re.search(pattern, message):
                return found_concerns

        # 第一人称表达关键词
        first_person_keywords = ['我觉得', '我感到', '我最近', '我总是', '我很', '我在']

        for category, keywords in self.PATTERNS['concerns'].items():
            for keyword in keywords:
                if keyword in message:
                    # 收集置信度因子
                    factors = {}

                    # 表达强度
                    if any(fpk in message for fpk in first_person_keywords):
                        factors['expression_strength'] = 0.8
                    else:
                        factors['expression_strength'] = 0.4

                    # 第一人称肯定
                    factors['first_person'] = ('我' in message[:30])

                    # 关键词特异性
                    factors['specificity'] = min(len(keyword) / 3.0, 1.0)

                    # 计算综合置信度
                    confidence = self._calculate_confidence(0.3, factors)
                    found_concerns[category] = confidence
                    break  # 每个类别只添加一次

        return found_concerns

    def _extract_preferences(self, message: str) -> Dict:
        """提取对话偏好"""
        prefs = {}

        # 对话长度偏好
        if '简单点' in message or '简短' in message or '短一点' in message:
            prefs['response_length'] = 'short'
        elif '详细' in message or '多说点' in message or '展开' in message:
            prefs['response_length'] = 'long'

        # 对话风格偏好
        if '专业' in message:
            prefs['response_style'] = 'professional'
        elif '随意' in message or '轻松' in message:
            prefs['response_style'] = 'casual'
        elif '温暖' in message:
            prefs['response_style'] = 'warm'

        # 主题偏好
        if '多问我' in message or '提问' in message:
            prefs['interaction_mode'] = 'question_based'
        elif '多听我说' in message or '只是倾诉' in message:
            prefs['interaction_mode'] = 'listening'

        return prefs

    def save_to_database(self):
        """保存画像到数据库（支持置信度和元数据）"""
        if not self.user:
            return False

        import json
        from models import db

        try:
            # 保存基本信息
            self.user.profile_name = self.profile['name']
            self.user.profile_age = self.profile['age']
            self.user.profile_job = self.profile['job']

            # 保存列表数据
            self.user.profile_hobbies = json.dumps(self.profile['hobbies'], ensure_ascii=False)
            self.user.profile_concerns = json.dumps(self.profile['concerns'], ensure_ascii=False)

            # 保存偏好设置（合并置信度和元数据）
            preferences_with_metadata = {
                'preferences': self.profile['preferences'],
                'confidence': self.profile.get('confidence', {}),
                'metadata': self.profile.get('metadata', {})
            }
            self.user.profile_preferences = json.dumps(preferences_with_metadata, ensure_ascii=False)

            # 保存更新时间
            if self.profile['last_updated']:
                self.user.profile_last_updated = datetime.fromisoformat(self.profile['last_updated'])

            db.session.commit()
            print(f"[用户画像] 保存成功 - 用户ID: {self.user.id}")
            return True
        except Exception as e:
            print(f"[用户画像] 保存失败: {e}")
            db.session.rollback()
            return False

    @classmethod
    def load_from_database(cls, user):
        """从数据库加载用户画像"""
        return cls(user)

    def get_prompt_context(self) -> str:
        """
        生成提示词上下文（平衡版 - 既具体又简洁）

        Returns:
            用户信息的文字描述
        """
        parts = []

        # 基本信息 - 简化表达
        if self.profile['age']:
            parts.append(f"{self.profile['age']}岁")

        if self.profile['job']:
            parts.append(self.profile['job'])  # 去掉"职业是"，更简洁

        # 爱好 - 保留前3个，使用具体关键词
        if self.profile['hobbies']:
            matched_keywords = self.profile['metadata'].get('matched_keywords', {}).get('hobbies', {})

            hobby_list = []
            for hobby in self.profile['hobbies'][:3]:  # 取前3个
                if hobby in matched_keywords and matched_keywords[hobby]:
                    # 使用具体的关键词
                    specific_keywords = matched_keywords[hobby][:2]  # 最多2个
                    hobby_list.extend(specific_keywords)
                else:
                    hobby_list.append(hobby)

            if hobby_list:
                parts.append('、'.join(hobby_list))

        # 困扰 - 只保留前2个最主要的
        if self.profile['concerns']:
            concerns_str = '、'.join(self.profile['concerns'][:2])
            parts.append(concerns_str)

        if parts:
            return "，".join(parts) + "。"
        else:
            return ""

    def get_adaptive_system_prompt(self, base_prompt: str) -> str:
        """
        根据用户画像生成自适应系统提示词

        Args:
            base_prompt: 基础系统提示词

        Returns:
            适配后的系统提示词
        """
        profile_context = self.get_prompt_context()

        # 获取用户偏好
        prefs = self.profile.get('preferences', {})

        # 保持原有结构：规则优先，画像在后补充
        prompt_parts = [base_prompt]

        # 如果有画像，在规则后追加用户背景和使用要求
        if profile_context:
            # 使用换行符分隔，保持清晰的结构
            prompt_parts.append(f"\n\n用户背景：{profile_context}")
            # 简短强调（不抢规则的风头）
            prompt_parts.append("注：回复时可结合上述信息给出更贴切的建议。")

        # 根据偏好调整
        if prefs.get('response_length') == 'short':
            prompt_parts.append("\n回复要求：简短精炼，控制在30-50字。")
        elif prefs.get('response_length') == 'long':
            prompt_parts.append("\n回复要求：详细展开，可以提供更多背景信息和建议。")

        if prefs.get('response_style') == 'professional':
            prompt_parts.append("\n对话风格：专业理性，提供科学依据。")
        elif prefs.get('response_style') == 'casual':
            prompt_parts.append("\n对话风格：轻松自然，像朋友聊天。")

        if prefs.get('interaction_mode') == 'question_based':
            prompt_parts.append("\n互动方式：多提出引导性问题，帮助用户自我探索。")
        elif prefs.get('interaction_mode') == 'listening':
            prompt_parts.append("\n互动方式：以倾听为主，给予共情和支持。")

        return ''.join(prompt_parts)

    def is_empty(self) -> bool:
        """检查画像是否为空"""
        return (
            not self.profile['name']
            and not self.profile['age']
            and not self.profile['job']
            and len(self.profile['hobbies']) == 0
            and len(self.profile['concerns']) == 0
        )

    def get_summary(self) -> str:
        """获取画像摘要（用于调试和展示）"""
        lines = []
        lines.append("=== 用户画像 ===")

        if self.profile['name']:
            lines.append(f"姓名: {self.profile['name']}")
        if self.profile['age']:
            lines.append(f"年龄: {self.profile['age']}")
        if self.profile['job']:
            lines.append(f"职业: {self.profile['job']}")
        if self.profile['hobbies']:
            lines.append(f"爱好: {', '.join(self.profile['hobbies'])}")
        if self.profile['concerns']:
            lines.append(f"困扰: {', '.join(self.profile['concerns'])}")
        if self.profile['preferences']:
            lines.append(f"偏好: {json.dumps(self.profile['preferences'], ensure_ascii=False)}")
        if self.profile['last_updated']:
            lines.append(f"更新时间: {self.profile['last_updated']}")

        if not any([self.profile['name'], self.profile['age'], self.profile['job'],
                   self.profile['hobbies'], self.profile['concerns']]):
            lines.append("（画像为空）")

        return '\n'.join(lines)

    def to_dict(self) -> Dict:
        """转换为字典（用于API返回）"""
        return self.profile.copy()


def build_prompt_with_profile(profile: UserProfile, user_message: str, base_prompt: str = None) -> str:
    """
    使用用户画像构建提示词

    Args:
        profile: 用户画像对象
        user_message: 当前用户消息
        base_prompt: 基础系统提示词（可选）

    Returns:
        系统提示词
    """
    if base_prompt is None:
        base_prompt = """你是温暖的陪伴助手。

规则:
1. 回复40字左右，不要超过60字
2. 不要"听起来""听上学"开头
3. 直接对话，适当关心
4. 结合用户之前提到的信息
5. 给予情感支持和实用建议"""

    # 使用自适应提示词生成
    return profile.get_adaptive_system_prompt(base_prompt)
