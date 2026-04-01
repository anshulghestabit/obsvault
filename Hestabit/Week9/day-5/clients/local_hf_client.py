from dataclasses import dataclass
from typing import Sequence

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


@dataclass
class LocalCreateResult:
    content: str


class LocalHFChatClient:
    def __init__(
        self,
        model_path: str,
        max_new_tokens: int = 180,
    ) -> None:
        self.model_path = model_path
        self.max_new_tokens = max_new_tokens

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32,
        )

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _messages_to_prompt(self, messages: Sequence[object]) -> str:
        system_blocks = []
        conversation_blocks = []

        for msg in messages:
            content = getattr(msg, "content", "")
            source = getattr(msg, "source", "unknown")
            class_name = msg.__class__.__name__.lower()

            if "system" in class_name:
                system_blocks.append(str(content).strip())
            elif "assistant" in class_name:
                conversation_blocks.append(f"ASSISTANT ({source}):\n{str(content).strip()}")
            else:
                conversation_blocks.append(f"USER ({source}):\n{str(content).strip()}")

        system_text = "\n\n".join(system_blocks).strip()
        conversation_text = "\n\n".join(conversation_blocks).strip()

        prompt = (
            "You must follow the system instructions exactly.\n\n"
            f"SYSTEM INSTRUCTIONS:\n{system_text}\n\n"
            f"CONVERSATION:\n{conversation_text}\n\n"
            "TASK:\n"
            "Write only the next assistant response.\n"
            "Do not create a multi-turn conversation.\n"
            "Do not add USER, ASSISTANT, Chatbot, or Research Agent labels.\n"
            "Do not continue beyond one response.\n\n"
            "ASSISTANT RESPONSE:\n"
        )
        return prompt

    async def create(self, messages: Sequence[object], cancellation_token=None) -> LocalCreateResult:
        prompt = self._messages_to_prompt(messages)

        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1,
            )

        decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        if decoded.startswith(prompt):
            decoded = decoded[len(prompt):]

        text = decoded.strip()

        stop_markers = [
            "\nUSER",
            "\nASSISTANT",
            "\nChatbot",
            "\nResearch Agent",
            "\nSummarizer Agent",
            "\nAnswer Agent",
        ]
        for marker in stop_markers:
            if marker in text:
                text = text.split(marker)[0].strip()

        return LocalCreateResult(content=text)

    async def close(self) -> None:
        pass