# app/services/llm_runtime/ollama_provider.py
import requests
from typing import List, Optional
from .provider_base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, model: str = "llama3.1:8b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def _post(self, endpoint: str, payload: dict):
        url = f"{self.host}/{endpoint}"
        res = requests.post(url, json=payload, timeout=90)
        res.raise_for_status()
        return res.json()

    def run(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or ""
        }
        data = self._post("api/generate", payload)
        return data.get("response", "")

    def run_batch(self, prompts: List[str]) -> List[str]:
        results = []
        for p in prompts:
            results.append(self.run(p))
        return results
