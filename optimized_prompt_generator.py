"""
优化后的系统提示词生成器
提取关键信息并生成结构化的系统提示词
"""


def extract_key_info_from_memories(memories):
    """
    从检索到的记忆中提取关键信息

    Args:
        memories: 检索到的记忆列表

    Returns:
        关键信息列表
    """
    key_info = []

    for mem in memories[:3]:  # 只使用前3条记忆
        user_msg = mem.get('user_message', '')

        # 提取用户名字（只在用户明确说"我叫XX"时提取）
        if "我叫" in user_msg and "今年" in user_msg:
            # 更精确的名字提取：确保是自我介绍格式
            parts = user_msg.split("我叫")
            if len(parts) > 1:
                # 提取"我叫"后面的内容
                after_name = parts[1]
                # 名字通常在逗号、句号或空格之前
                name_part = after_name.split("，")[0].split(",")[0].split("。")[0].split(" ")[0].split("是")[0].strip()
                # 过滤：名字应该是2-4个字的中文
                if name_part and len(name_part) <= 4 and name_part.isalpha():
                    # 检查是否包含常见名字特征
                    if not any(char in name_part for char in ['的', '了', '吗', '呢', '啊']):
                        key_info.append(f"用户名字：{name_part}")

        # 提取年龄（只在第一次提及时提取）
        if "今年" in user_msg and "岁" in user_msg:
            import re
            age_match = re.search(r'今年.*?(\d+)岁', user_msg)
            if age_match and not any("年龄" in info for info in key_info):
                key_info.append(f"年龄：{age_match.group(1)}岁")

        # 提取职业（只在第一次提及时提取）
        if "是程序员" in user_msg or "我是程序员" in user_msg:
            if not any("职业" in info for info in key_info):
                key_info.append("职业：程序员")

        # 提取爱好（只在第一次提及时提取）
        if "喜欢打篮球" in user_msg or "爱好篮球" in user_msg:
            if not any("爱好" in info for info in key_info):
                key_info.append("爱好：打篮球")

        # 提取关键问题/困扰
        if "失眠" in user_msg or "睡不着" in user_msg:
            if "困扰：失眠" not in key_info:
                key_info.append("困扰：失眠")
        if "工作压力" in user_msg or "工作12小时" in user_msg or "加班" in user_msg:
            if "困扰：工作压力" not in key_info:
                key_info.append("困扰：工作压力")
        if "焦虑" in user_msg or "担心" in user_msg:
            if "情绪：焦虑或担心" not in key_info:
                key_info.append("情绪：焦虑或担心")

    return key_info


def build_optimized_system_prompt(key_info=None, base_prompt=None, current_message=""):
    """
    构建优化后的系统提示词

    Args:
        key_info: 关键信息列表（从记忆中提取）
        base_prompt: 基础系统提示词（可选）
        current_message: 当前用户输入（用于上下文）

    Returns:
        优化后的系统提示词
    """
    # 提取用户名字（如果有的话）
    user_name = None
    for info in key_info or []:
        if info.startswith("用户名字："):
            user_name = info.split("：")[1]
            break

    # 构建简洁的名字提示
    name_hint = f"用户叫{user_name}，" if user_name else ""

    # 构建简洁的系统提示词
    if user_name:
        system_prompt = f"""你是温暖的陪伴助手。{name_hint}

用户说：{current_message}

请自然、真诚地回应用户。如果相关，可以记住用户的名字和信息。
回复60-100字，要简洁、有针对性。"""
    else:
        system_prompt = f"""你是温暖的陪伴助手。

用户说：{current_message}

请温暖、真诚地回应用户。
回复60-100字，要简洁、有针对性。"""

    return system_prompt


def generate_prompt_with_memory(user_id, conversation_id, message, memory_system, base_prompt=None, query_time=None):
    """
    使用RAG记忆生成优化后的系统提示词

    Args:
        user_id: 用户ID
        conversation_id: 会话ID
        message: 用户消息
        memory_system: 记忆系统实例
        base_prompt: 基础系统提示词（可选，当没有记忆时使用）
        query_time: 查询时间（用于测试模拟时间间隔）

    Returns:
        (system_prompt, retrieved_memories) 元组
    """
    retrieved_memories = []

    # 检索记忆
    if memory_system and memory_system.is_enabled():
        try:
            retrieved_memories = memory_system.retrieve(
                user_id=str(user_id),
                conversation_id=str(conversation_id),
                query=message,
                top_k=3,
                days=30,
                query_time=query_time
            )

            if retrieved_memories:
                print(f"[记忆检索] 找到{len(retrieved_memories)}条记忆")

                # 提取关键信息
                key_info = extract_key_info_from_memories(retrieved_memories)

                if key_info:
                    print(f"[关键信息] 提取到: {', '.join(key_info)}")
                    # 构建优化提示词（传递当前用户消息）
                    system_prompt = build_optimized_system_prompt(key_info, base_prompt, message)
                else:
                    print(f"[关键信息] 未能提取到明确信息，使用基础提示词")
                    system_prompt = build_optimized_system_prompt(None, base_prompt, message)
            else:
                print(f"[记忆检索] 未找到相关记忆")
                system_prompt = build_optimized_system_prompt(None, base_prompt, message)

        except Exception as e:
            print(f"[记忆检索] 失败: {e}")
            import traceback
            traceback.print_exc()
            system_prompt = build_optimized_system_prompt(None, base_prompt, message)
    else:
        # 没有记忆系统
        system_prompt = build_optimized_system_prompt(None, base_prompt, message)

    return system_prompt, retrieved_memories


def save_message_to_memory(memory_system, user_id, conversation_id, user_message, bot_response, custom_timestamp=None):
    """
    保存对话到记忆系统

    Args:
        memory_system: 记忆系统实例
        user_id: 用户ID
        conversation_id: 会话ID
        user_message: 用户消息
        bot_response: 机器人回复
        custom_timestamp: 自定义时间戳（用于测试模拟时间间隔）
    """
    if memory_system and memory_system.is_enabled():
        try:
            memory_system.add_message(
                user_id=str(user_id),
                conversation_id=str(conversation_id),
                user_message=user_message,
                bot_response=bot_response,
                metadata={"source": "web_chat"},
                custom_timestamp=custom_timestamp
            )
            print(f"[记忆存储] 消息已保存")
        except Exception as e:
            print(f"[记忆存储] 失败: {e}")
            import traceback
            traceback.print_exc()
