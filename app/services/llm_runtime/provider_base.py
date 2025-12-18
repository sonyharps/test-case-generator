# app/services/llm_runtime/provider_base.py
from abc import ABC, abstractmethod
from typing import Optional, List


class LLMProvider(ABC):
    """Abstract LLM provider definition."""

    @abstractmethod
    def run(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Run a prompt and return a string."""
        pass

    @abstractmethod
    def run_batch(self, prompts: List[str]) -> List[str]:
        """Run multiple prompts in batch."""
        pass
