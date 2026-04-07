# -*- coding: utf-8 -*-
"""
用户画像系统 - 简单、直接的用户信息管理
"""

import re
from typing import Dict, Optional, List


class UserProfile:
    """用户画像"""

    def __init__(self):
        self.profile = {
            "name": None,
            "age": None,
            "job": None,
            "hobbies": [],
            "concerns": [],  # 困扰/问题
        }

    def extract_from_first_message(self, message: str) -> bool:
        """
        从第一条消息中提取用户信息

        Args:
            message: 用户的第一条消息

        Returns:
            是否成功提取到信息
        """
        updated = False

        # 提取名字
        if "我叫" in message:
            try:
                name_part = message.split("我叫")[1].split("，")[0].split(",")[0].split("。")[0].strip()
                if name_part and len(name_part) <= 4 and name_part.isalpha():
                    self.profile["name"] = name_part
                    updated = True
            except:
                pass

        # 提取年龄
        age_match = re.search(r'(\d+)岁', message)
        if age_match:
            self.profile["age"] = int(age_match.group(1))
            updated = True

        # 提取职业
        if "程序员" in message:
            self.profile["job"] = "程序员"
            updated = True
        elif "医生" in message:
            self.profile["job"] = "医生"
            updated = True
        elif "老师" in message:
            self.profile["job"] = "老师"
            updated = True

        # 提取爱好
        if "打篮球" in message or "篮球" in message:
            if "篮球" not in self.profile["hobbies"]:
                self.profile["hobbies"].append("篮球")
                updated = True
        elif "跑步" in message:
            if "跑步" not in self.profile["hobbies"]:
                self.profile["hobbies"].append("跑步")
                updated = True
        elif "游泳" in message:
            if "游泳" not in self.profile["hobbies"]:
                self.profile["hobbies"].append("游泳")
                updated = True

        # 提取困扰
        if "失眠" in message:
            if "失眠" not in self.profile["concerns"]:
                self.profile["concerns"].append("失眠")
                updated = True
        if "工作压力" in message:
            if "工作压力" not in self.profile["concerns"]:
                self.profile["concerns"].append("工作压力")
                updated = True

        return updated

    def get_prompt_context(self) -> str:
        """
        生成提示词上下文

        Returns:
            用户信息的文字描述
        """
        parts = []

        if self.profile["name"]:
            parts.append(f"用户叫{self.profile['name']}")

        if self.profile["age"]:
            parts.append(f"{self.profile['age']}岁")

        if self.profile["job"]:
            parts.append(f"是{self.profile['job']}")

        if self.profile["hobbies"]:
            parts.append(f"喜欢{self.profile['hobbies']}")

        if parts:
            return "，".join(parts) + "。"
        else:
            return ""

    def is_empty(self) -> bool:
        """检查画像是否为空"""
        return (
            not self.profile["name"]
            and not self.profile["age"]
            and not self.profile["job"]
            and len(self.profile["hobbies"]) == 0
        )

    def get_summary(self) -> str:
        """获取画像摘要（用于调试）"""
        return str(self.profile)


def build_prompt_with_profile(profile: UserProfile, user_message: str) -> str:
    """
    使用用户画像构建提示词

    Args:
        profile: 用户画像对象
        user_message: 当前用户消息

    Returns:
        系统提示词
    """
    profile_context = profile.get_prompt_context()

    if profile_context:
        return f"""你是温暖的陪伴助手。

{profile_context}

用户说：{user_message}

请真诚、自然地回应用户。如果相关，可以记住并使用用户的信息。
回复60-100字，要简洁、有针对性。"""
    else:
        return f"""你是温暖的陪伴助手。

用户说：{user_message}

请温暖、真诚地回应用户。
回复60-100字，要简洁、有针对性。"""
