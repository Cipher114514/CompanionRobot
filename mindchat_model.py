"""
简化的 MindChat 对话模型实现 - 精简版
固定 prompt，对话输出只和输入有关，不依赖历史
"""

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Optional


class MindChatDialogue:
    """MindChat 对话模型 - 精简版（无历史依赖）"""

    def __init__(self, model_path: str = "./models/qwen2-1.5b-instruct/Qwen/qwen2-1.5b-instruct"):
        """
        初始化 MindChat 对话模型

        Args:
            model_path: 模型路径
        """
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

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

    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        max_length: int = 80,
        temperature: float = 0.8,
        user_id: Optional[int] = None
    ) -> str:
        """
        进行对话（精简版：不使用历史，只基于当前输入）

        Args:
            message: 用户消息
            system_prompt: 系统 prompt（可选）
            max_length: 最大生成长度（tokens），设置为80以支持40字左右的回复
            temperature: 温度参数
            user_id: 用户ID（保留接口兼容性，实际不使用）

        Returns:
            模型响应文本
        """
        if not self.model or not self.tokenizer:
            return "抱歉，对话模型未加载。"

        try:
            # 使用 Qwen2 的 ChatML 格式
            messages = []

            # 添加 system prompt
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                # 默认的陪伴角色 - 心理咨询师模式
                messages.append({
                    "role": "system",
                    "content": """你是温暖的心理陪伴者。回复要求：
1. 必须2-3句话，50字以内
2. 不要"听起来""听上去"开头
3. 不要列1.2.3.建议
4. 直接表达理解和关心"""
                })

            # 添加当前用户消息（不使用历史）
            messages.append({"role": "user", "content": message})

            # 使用 tokenizer 的 chat 模板
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # 编码
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)

            # 限制输出长度：避免截断，让模型完整输出
            # 512 tokens 确保回复完整，模型会在适当时候自然停止
            actual_max_new_tokens = 512

            # 生成参数 - 极简快速
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=actual_max_new_tokens,
                    temperature=temperature,
                    do_sample=False,  # 关闭采样，直接用贪婪解码，更快
                    top_k=1,  # 贪婪解码
                    repetition_penalty=1.0,
                    pad_token_id=self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            # 解码
            response = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )

            # 清理响应
            response = response.strip()

            # 只去除完全相同且连续的行
            lines = response.split('\n')
            cleaned_lines = []
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and (not cleaned_lines or line_stripped != cleaned_lines[-1]):
                    cleaned_lines.append(line_stripped)

            response = '\n'.join(cleaned_lines).strip()

            # 调试输出
            print(f"[MindChat] 响应长度: {len(response)} 字符")

            # 只在明显异常时才补充（空回复或只有标点）
            if not response.strip() or len(response.strip()) < 15:
                print(f"[MindChat] 响应异常，使用默认回复")
                response = "我听到了你的感受。请告诉我更多，我会尽力帮助你。"

            return response

        except Exception as e:
            print(f"[MindChat] 对话生成失败: {e}")
            import traceback
            traceback.print_exc()
            return f"抱歉，生成回复时出错：{str(e)}"

    def clear_history(self, user_id: Optional[int] = None):
        """
        清除对话历史（精简版：无操作，因为不使用历史）

        Args:
            user_id: 用户ID（保留接口兼容性）
        """
        pass  # 不使用历史，无需清除
