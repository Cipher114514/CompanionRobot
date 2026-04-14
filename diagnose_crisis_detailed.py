# -*- coding: utf-8 -*-
"""
危机干预详细诊断脚本
找出为什么最终回复是"抱歉，我遇到了一些问题"
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("危机干预详细诊断".center(80))
print("=" * 80)

# 1. 模拟完整的危机检测和干预流程
print("\n【步骤1】初始化模块")
print("-" * 80)

from crisis_detection import CrisisDetector, CrisisResponder

detector = CrisisDetector()
responder = CrisisResponder()  # USE_AI_GENERATION=True

print("✓ 危机检测器初始化成功")
print(f"  - USE_AI_GENERATION: {responder.config.USE_AI_GENERATION}")
print(f"  - ai_generator: {responder.ai_generator}")

# 2. 模拟用户输入
print("\n【步骤2】模拟用户输入'我想自杀'")
print("-" * 80)

user_input = "我想自杀"
user_id = 4  # 使用用户日志中的user_id

print(f"用户输入: {user_input}")
print(f"用户ID: {user_id}")

# 3. 危机检测
print("\n【步骤3】执行危机检测")
print("-" * 80)

detection_result = detector.detect(user_input, user_id)

print(f"检测结果:")
print(f"  - is_crisis: {detection_result.is_crisis}")
print(f"  - level: {detection_result.level}")
print(f"  - confidence: {detection_result.confidence}")
print(f"  - keywords: {detection_result.keywords}")
print(f"  - suggested_action: {detection_result.suggested_action}")

# 4. 生成干预（关键步骤）
print("\n【步骤4】生成危机干预回复")
print("-" * 80)

print("调用 crisis_responder.generate()...")

try:
    intervention = responder.generate(
        level=detection_result.level,
        keywords=detection_result.keywords,
        emotion="negative",
        user_input=user_input,
        user_context={"user_id": user_id}
    )

    print("✓ intervention对象生成成功")
    print(f"  - 类型: {type(intervention)}")
    print(f"  - should_cover: {intervention.should_cover}")
    print(f"  - is_ai_generated: {intervention.is_ai_generated}")
    print(f"  - content长度: {len(intervention.content) if intervention.content else 0}")
    print(f"  - content值: {repr(intervention.content)}")
    print(f"  - resources数量: {len(intervention.resources)}")

    # 5. 验证content
    print("\n【步骤5】验证干预内容")
    print("-" * 80)

    content = intervention.content

    print(f"content类型: {type(content)}")
    print(f"content是否为None: {content is None}")
    print(f"content是否为空: {not content if content else False}")

    if content:
        print(f"content长度: {len(content)}")
        print(f"content前100字符: {content[:100]}")

        # 检查是否是错误消息
        error_messages = ["抱歉，我遇到了一些问题", "抱歉，生成回复时出错"]
        is_error = any(msg in content for msg in error_messages)
        print(f"是否包含错误消息: {is_error}")

        if is_error:
            print("⚠️ 检测到错误消息！")
        else:
            print("✓ content看起来正常")

    # 6. 模拟flask_app.py的逻辑
    print("\n【步骤6】模拟flask_app.py逻辑")
    print("-" * 80)

    print("执行: if intervention.should_cover:")
    if intervention.should_cover:
        print("  → should_cover = True")
        print(f"  → response = intervention.content")
        response = intervention.content
        print(f"  → 准备返回的response: {repr(response)}")

        # 检查response
        if not response:
            print("  ⚠️ response为空！")
        elif len(response) < 10:
            print(f"  ⚠️ response过短: {len(response)}")
        elif "抱歉，我遇到了一些问题" in response:
            print("  ⚠️ response包含错误消息！")
        else:
            print(f"  ✓ response正常，长度: {len(response)}")

    else:
        print("  → should_cover = False，不会覆盖")

except Exception as e:
    print(f"✗ 发生异常: {e}")
    import traceback
    traceback.print_exc()

# 7. 对比测试
print("\n【步骤7】对比测试：AI生成 vs 模板")
print("-" * 80)

print("测试1: 使用AI生成")
print("-" * 40)

try:
    from mindchat_dialogue import IntegratedMindChatSystem
    system = IntegratedMindChatSystem()

    prompt = f"""你是一个温暖的心理陪伴助手。用户可能处于心理困扰中。

【用户输入】{user_input}
【用户情绪】negative

【回应要求】
1. 表达担忧，提供专业帮助资源信息
2. 语言温暖自然，像朋友而非机器
3. 不要说"检测到"、"分析"这类机械话
4. 不要强制用户，保留选择权
5. 长度50-150字
6. 延续对话，不要终结

请生成回应："""

    ai_response = system.generate_response(prompt, {"user_id": user_id})
    print(f"✓ AI生成成功")
    print(f"  长度: {len(ai_response)}")
    print(f"  内容: {repr(ai_response)}")

except Exception as e:
    print(f"✗ AI生成失败: {e}")

print("\n测试2: 使用模板")
print("-" * 40)

template_response = responder._generate_by_template(3, "negative")
print(f"✓ 模板生成成功")
print(f"  长度: {len(template_response)}")
print(f"  内容: {repr(template_response)}")

# 8. 关键验证
print("\n【步骤8】关键验证")
print("-" * 80)

print("验证1: AI生成是否返回错误消息？")
if ai_response:
    has_error = "抱歉，我遇到了一些问题" in ai_response
    print(f"  {'✗ 是' if has_error else '✓ 否'}")

print("\n验证2: 模板是否返回错误消息？")
if template_response:
    has_error = "抱歉，我遇到了一些问题" in template_response
    print(f"  {'✗ 是' if has_error else '✓ 否'}")

print("\n验证3: intervention.content使用的是哪个？")
if intervention:
    if intervention.is_ai_generated:
        print("  → 使用AI生成")
    else:
        print("  → 使用模板")

print("\n" + "=" * 80)
print("诊断完成".center(80))
print("=" * 80)

print("\n【建议】")
print("如果intervention.content包含错误消息，问题可能在于：")
print("  1. AI生成时返回了错误")
print("  2. prompt或context参数传递错误")
print("  3. mindchat_system.generate_response的实现有问题")
print()
print("需要添加日志来追踪实际运行时的行为。")
