# app/services/llm_runtime/runtime_factory.py
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .provider_base import LLMProvider


def get_llm_provider(model: str) -> LLMProvider:
    """
    Auto-select provider based on model name.
    - model startswith "llama" or "phi" -> Ollama
    - model startswith "gpt" or "o"     -> OpenAI
    - you can extend easily for Groq / Mistral / etc
    """

    m = model.lower()

    if any(key in m for key in ["llama", "phi", "mistral", "ministral"]):
        return OllamaProvider(model=model)

    if any(key in m for key in ["gpt", "o1", "openai"]):
        return OpenAIProvider(model=model)

    # default fallback local model
    return OllamaProvider(model=model)
