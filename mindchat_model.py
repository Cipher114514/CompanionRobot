"""
简化的 MindChat 对话模型实现
"""

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Optional


class MindChatDialogue:
    """MindChat 对话模型 - 简化实现"""

    def __init__(self, model_path: str = "./models/qwen2-1.5b-instruct/Qwen/qwen2-1___5b-instruct"):
        """
        初始化 MindChat 对话模型

        Args:
            model_path: 模型路径
        """
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # 用户隔离的对话历史 {user_id: [messages]}
        self.conversation_histories = {}
        self.max_history_length = 4  # 保留最近2轮对话（4条消息：用户+助手×2）
        self.current_user_id = None  # 当前对话的用户ID

        try:
            print(f"[MindChat] 正在加载模型: {model_path}")
            print(f"[MindChat] 使用设备: {self.device}")

            # 加载 tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )

            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )

            if self.device == "cpu":
                self.model = self.model.to(self.device)

            print("[MindChat] 模型加载成功")

        except Exception as e:
            print(f"[MindChat] 模型加载失败: {e}")
            self.model = None
            self.tokenizer = None

    def _get_user_history(self, user_id: int) -> list:
        """获取指定用户的对话历史"""
        if user_id not in self.conversation_histories:
            self.conversation_histories[user_id] = []
        return self.conversation_histories[user_id]

    def set_user(self, user_id: int):
        """设置当前用户ID"""
        self.current_user_id = user_id

    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        max_length: int = 512,
        temperature: float = 0.7,
        user_id: Optional[int] = None
    ) -> str:
        """
        进行对话

        Args:
            message: 用户消息
            system_prompt: 系统 prompt（可选）
            max_length: 最大生成长度（tokens）
            temperature: 温度参数
            user_id: 用户ID（用于隔离对话历史）

        Returns:
            模型响应文本
        """
        if not self.model or not self.tokenizer:
            return "抱歉，对话模型未加载。"

        # 设置用户ID
        if user_id:
            self.set_user(user_id)
        elif not self.current_user_id:
            # 如果没有指定用户ID，使用默认ID（用于测试）
            self.current_user_id = 0

        # 获取该用户的对话历史
        conversation_history = self._get_user_history(self.current_user_id)

        try:
            # 使用 Qwen2 的 ChatML 格式
            messages = []

            # 添加 system prompt
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                # 默认的温和陪伴角色
                messages.append({
                    "role": "system",
                    "content": """你是一位温暖、专业的心理咨询陪伴助手。

回复要求（重要）：
1. 首先简短共情（1句话，15字内）
2. 然后给出2个具体方法（每个方法20字内）
3. 最后鼓励支持（1句话，15字内）
4. 总共60-100字，必须简洁

注意：回复必须简洁完整，不要啰嗦，直接说重点。"""
                })

            # 添加该用户的对话历史（最近2轮）
            messages.extend(conversation_history)

            # 添加当前用户消息
            messages.append({"role": "user", "content": message})

            # 使用 tokenizer 的 chat 模板
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # 编码
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)

            # 根据max_length参数动态设置生成参数
            # 对于长文本生成（如报告），使用更大的max_new_tokens
            actual_max_new_tokens = min(max_length, 2048)  # 最大不超过2048

            # 生成参数
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=actual_max_new_tokens,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    top_k=40,
                    repetition_penalty=1.1,
                    num_beams=1,
                    early_stopping=False,
                    pad_token_id=self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            # 解码
            response = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )

            # 清理响应 - 优化版，避免截断
            response = response.strip()

            # 只去除完全相同且连续的行
            lines = response.split('\n')
            cleaned_lines = []
            for line in lines:
                line_stripped = line.strip()
                # 只保留非空行，且不与上一行完全相同
                if line_stripped and (not cleaned_lines or line_stripped != cleaned_lines[-1]):
                    cleaned_lines.append(line_stripped)

            response = '\n'.join(cleaned_lines).strip()

            # 调试输出
            print(f"[MindChat] 用户ID: {self.current_user_id}")
            print(f"[MindChat] 原始响应长度: {len(response)} 字符")
            print(f"[MindChat] 对话轮次: {len(conversation_history) // 2}")
            print(f"[MindChat] 响应内容: {response[:100]}...")

            # 确保回复有实质内容且完整
            if len(response) < 30:
                print(f"[MindChat] ⚠️ 响应过短，进行补充")
                response = f"我听到了你的感受。{response}能和我说说更多关于这件事的情况吗？"

            # 保存到该用户的历史（维护滑动窗口）
            conversation_history.append({"role": "user", "content": message})
            conversation_history.append({"role": "assistant", "content": response})

            # 只保留最近2轮对话（4条消息），防止token占用过多
            if len(conversation_history) > self.max_history_length:
                self.conversation_histories[self.current_user_id] = conversation_history[-self.max_history_length:]

            return response

        except Exception as e:
            print(f"[MindChat] 对话生成失败: {e}")
            import traceback
            traceback.print_exc()
            return f"抱歉，生成回复时出错：{str(e)}"

    def clear_history(self, user_id: Optional[int] = None):
        """
        清除对话历史

        Args:
            user_id: 要清除的用户ID，如果为None则清除当前用户的历史
        """
        target_user_id = user_id if user_id is not None else self.current_user_id
        if target_user_id in self.conversation_histories:
            self.conversation_histories[target_user_id] = []
            print(f"[MindChat] 已清除用户 {target_user_id} 的对话历史")
