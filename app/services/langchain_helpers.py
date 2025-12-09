# app/services/langchain_helpers.py
from app.utils.llm_client import ollama_generate

class OllamaLLMWrapper:
    """
    Minimal wrapper so orchestrator calls model uniformly.
    Returns raw text (string) from ollama_generate.
    """
    def __init__(self, model: str = "llama3.1:8b"):
        self.model = model

    def __call__(self, prompt: str) -> str:
        return ollama_generate(model=self.model, prompt=prompt)
