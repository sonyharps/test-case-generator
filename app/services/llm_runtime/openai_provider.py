# app/services/llm_runtime/openai_provider.py
from typing import List, Optional
from openai import OpenAI
from .provider_base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4.1", api_key: str = None, base_url: str = None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def run(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        msg = []
        if system_prompt:
            msg.append({"role": "system", "content": system_prompt})
        msg.append({"role": "user", "content": prompt})

        res = self.client.chat.completions.create(
            model=self.model,
            messages=msg,
            temperature=0
        )
        return res.choices[0].message["content"]

    def run_batch(self, prompts: List[str]) -> List[str]:
        out = []
        for p in prompts:
            out.append(self.run(p))
        return out
