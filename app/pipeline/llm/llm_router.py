"""
Simple LLM router for backward compatibility.
For new features, use multi_llm_router instead.
"""

from .client_ollama import OllamaClient
from .glm_client import GLMClient


def get_llm_client(model: str):
    """
    Get LLM client based on model name.

    Auto-detects provider:
    - GLM models: glm-4-plus, glm-4-flash, chatglm, etc.
    - Everything else: Ollama (llama3.1, mistral, phi, etc.)
    """
    model_lower = model.lower()

    # GLM API models
    if any(key in model_lower for key in ["glm", "chatglm"]):
        return GLMClient(model)

    # Default to Ollama for all other models
    return OllamaClient(model)
