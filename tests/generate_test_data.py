# -*- coding: utf-8 -*-
"""
测试数据生成器

生成模拟的用户多轮对话数据，用于测试报告生成和仪表盘功能
"""

import sys
import os
import json
from datetime import datetime, timedelta
import random

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDataGenerator:
    """测试数据生成器"""

    def __init__(self):
        """初始化生成器"""
        self.test_users = []
        self.conversations = []

    def generate_test_users(self, count=3):
        """
        生成测试用户数据

        参数:
            count: 生成用户数量

        返回:
            用户列表
        """
        user_templates = [
            {
                "username": "test_user_1",
                "password": "password123",
                "email": "test1@example.com",
                "role": "patient",
                "name": "小明",
                "age": 25,
                "gender": "男",
                "profile": "软件工程师，工作压力大"
            },
            {
                "username": "test_user_2",
                "password": "password123",
                "email": "test2@example.com",
                "role": "patient",
                "name": "小红",
                "age": 22,
                "gender": "女",
                "profile": "大学生，面临就业压力"
            },
            {
                "username": "test_counselor",
                "password": "password123",
                "email": "counselor@example.com",
                "role": "counselor",
                "name": "王咨询师",
                "age": 35,
                "gender": "女",
                "profile": "心理咨询师，专业认证"
            }
        ]

        users = []
        for i in range(min(count, len(user_templates))):
            users.append(user_templates[i])

        self.test_users = users
        return users

    def generate_conversation_data(self, user_id, days_span=7, conversations_per_day=2):
        """
        生成模拟对话数据

        参数:
            user_id: 用户ID
            days_span: 跨越天数
            conversations_per_day: 每天对话次数

        返回:
            对话列表
        """
        # 模拟对话模板
        conversation_templates = [
            # 工作压力相关
            {
                "user_message": "今天工作太累了，感觉压力很大",
                "bot_response": "听起来你今天确实很辛苦。工作中发生了什么特别的事情吗？",
                "sentiment": "negative",
                "emotion_keywords": ["累", "压力"]
            },
            {
                "user_message": "老板今天又给我加了很多任务，我真的做不完",
                "bot_response": "被突然增加任务确实会让人感到焦虑。你觉得这些任务中最困难的是哪部分？",
                "sentiment": "negative",
                "emotion_keywords": ["焦虑", "无助"]
            },
            {
                "user_message": "我可能需要和老板沟通一下，但是又怕他生气",
                "bot_response": "理解你的担心。沟通工作量和预期是很重要的，也许我们可以一起想想怎么表达会更好。",
                "sentiment": "negative",
                "emotion_keywords": ["担心", "矛盾"]
            },

            # 失眠相关
            {
                "user_message": "我最近失眠很严重，整晚都睡不着",
                "bot_response": "失眠确实很让人难受。这种情况持续多久了？",
                "sentiment": "negative",
                "emotion_keywords": ["失眠", "疲惫"]
            },
            {
                "user_message": "大概有两周了，每晚都要到凌晨两三点才能睡着",
                "bot_response": "两周的失眠确实需要重视。你睡前一般会做什么呢？",
                "sentiment": "negative",
                "emotion_keywords": ["焦虑", "痛苦"]
            },
            {
                "user_message": "一直在刷手机，脑子停不下来想工作的事",
                "bot_response": "睡前刷手机和想工作确实会影响睡眠。我们可以尝试一些放松的睡前活动。",
                "sentiment": "negative",
                "emotion_keywords": ["焦虑", "不安"]
            },

            # 情绪低落
            {
                "user_message": "最近心情很不好，感觉很孤独",
                "bot_response": "听到你这么说我很关心你。这种孤独感是什么时候开始的呢？",
                "sentiment": "negative",
                "emotion_keywords": ["孤独", "低落"]
            },
            {
                "user_message": "自从换了新工作后，就没有朋友可以说话了",
                "bot_response": "环境变化确实会影响社交。你有尝试过认识新朋友或者和老朋友保持联系吗？",
                "sentiment": "negative",
                "emotion_keywords": ["孤独", "想念"]
            },

            # 积极改善
            {
                "user_message": "今天尝试了你的建议，晚饭后出去散步了",
                "bot_response": "太好了！散步确实能帮助放松心情。散步时感觉怎么样？",
                "sentiment": "positive",
                "emotion_keywords": ["放松", "开心"]
            },
            {
                "user_message": "感觉还不错，心情好了一些，也容易入睡了",
                "bot_response": "这真是个好消息！保持下去，你会越来越好的。",
                "sentiment": "positive",
                "emotion_keywords": ["开心", "希望"]
            },

            # 寻求建议
            {
                "user_message": "你能给我一些建议吗？我该怎么应对这些压力？",
                "bot_response": "当然可以。首先，尝试把大任务分解成小步骤，每次专注一个。其次，记得给自己安排休息时间。",
                "sentiment": "neutral",
                "emotion_keywords": ["寻求", "期待"]
            },
            {
                "user_message": "谢谢你的建议，我会试试的",
                "bot_response": "不客气，慢慢来，我相信你能应对这些挑战的。",
                "sentiment": "positive",
                "emotion_keywords": ["感激", "鼓励"]
            }
        ]

        conversations = []
        base_time = datetime.now() - timedelta(days=days_span)

        for day in range(days_span):
            for conv_num in range(conversations_per_day):
                # 随机选择一个对话模板
                template = random.choice(conversation_templates)

                # 计算时间
                hour = random.randint(9, 22)
                minute = random.randint(0, 59)
                msg_time = base_time + timedelta(
                    days=day,
                    hours=hour,
                    minutes=minute
                )

                conversation = {
                    "user_id": user_id,
                    "user_message": template["user_message"],
                    "bot_response": template["bot_response"],
                    "sentiment": template["sentiment"],
                    "emotion_keywords": template["emotion_keywords"],
                    "timestamp": msg_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "message_type": "text"
                }

                conversations.append(conversation)

        # 按时间排序
        conversations.sort(key=lambda x: x["timestamp"])

        return conversations

    def generate_sentiment_analysis(self, conversations):
        """
        生成情绪分析数据

        参数:
            conversations: 对话列表

        返回:
            情绪分析记录列表
        """
        sentiment_records = []

        for conv in conversations:
            record = {
                "user_id": conv["user_id"],
                "message_id": len(sentiment_records) + 1,
                "sentiment": conv["sentiment"],
                "confidence": round(random.uniform(0.7, 0.95), 3),
                "emotion_keywords": conv["emotion_keywords"],
                "timestamp": conv["timestamp"]
            }
            sentiment_records.append(record)

        return sentiment_records

    def save_to_json(self, data, filename):
        """
        保存数据到JSON文件

        参数:
            data: 要保存的数据
            filename: 文件名
        """
        output_dir = "tests/test_data"
        os.makedirs(output_dir, exist_ok=True)

        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[OK] 数据已保存: {filepath}")
        return filepath

    def generate_full_test_dataset(self):
        """
        生成完整的测试数据集
        """
        print("="*80)
        print("测试数据生成器")
        print("="*80)

        # 1. 生成用户数据
        print("\n[1/4] 生成测试用户...")
        users = self.generate_test_users(count=3)
        users_file = self.save_to_json(users, "test_users.json")
        print(f"    已生成 {len(users)} 个测试用户")

        # 2. 为每个患者用户生成对话数据
        print("\n[2/4] 生成对话数据...")
        all_conversations = []
        all_sentiments = []

        for user in users:
            if user["role"] == "patient":
                print(f"    为用户 {user['name']} 生成对话...")
                # 模拟 user_id (假设从1开始)
                user_id = users.index(user) + 1

                # 生成7天的对话，每天2-3次
                conversations = self.generate_conversation_data(
                    user_id=user_id,
                    days_span=7,
                    conversations_per_day=random.randint(2, 3)
                )

                all_conversations.extend(conversations)

                # 生成情绪分析数据
                sentiments = self.generate_sentiment_analysis(conversations)
                all_sentiments.extend(sentiments)

                print(f"      生成了 {len(conversations)} 条对话")

        conversations_file = self.save_to_json(all_conversations, "test_conversations.json")
        sentiments_file = self.save_to_json(all_sentiments, "test_sentiment_records.json")
        print(f"    总计: {len(all_conversations)} 条对话, {len(all_sentiments)} 条情绪记录")

        # 3. 生成统计摘要
        print("\n[3/4] 生成统计摘要...")
        summary = {
            "generation_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "users": {
                "total": len(users),
                "patients": sum(1 for u in users if u["role"] == "patient"),
                "counselors": sum(1 for u in users if u["role"] == "counselor")
            },
            "conversations": {
                "total": len(all_conversations),
                "days_span": 7,
                "avg_per_day": len(all_conversations) / 7
            },
            "sentiments": {
                "total": len(all_sentiments),
                "positive": sum(1 for s in all_sentiments if s["sentiment"] == "positive"),
                "negative": sum(1 for s in all_sentiments if s["sentiment"] == "negative"),
                "neutral": sum(1 for s in all_sentiments if s["sentiment"] == "neutral")
            }
        }

        summary_file = self.save_to_json(summary, "test_data_summary.json")
        print(f"    正面: {summary['sentiments']['positive']}, "
              f"负面: {summary['sentiments']['negative']}, "
              f"中性: {summary['sentiments']['neutral']}")

        # 4. 打印汇总
        print("\n[4/4] 生成完成")
        print("\n生成的文件:")
        print(f"  - {users_file}")
        print(f"  - {conversations_file}")
        print(f"  - {sentiments_file}")
        print(f"  - {summary_file}")
        print(f"\n数据目录: tests/test_data/")

        return {
            "users": users,
            "conversations": all_conversations,
            "sentiments": all_sentiments,
            "summary": summary
        }


def main():
    """主函数"""
    generator = TestDataGenerator()
    return generator.generate_full_test_dataset()


if __name__ == "__main__":
    main()
