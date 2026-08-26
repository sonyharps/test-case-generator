"""
Legacy LLM router — now a thin compatibility shim.

Previously this module auto-detected only Ollama/GLM and hardcoded
`llama3.1:8b` as the local fallback. It has been replaced by a delegation to
`multi_llm_router.get_llm_client()`, which supports all providers
(Ollama, GLM, Groq, Gemini) via model-string auto-detection.

Existing call sites (orchestrator_v7, pdf_adapter, advanced_rag_service, etc.)
keep importing `get_llm_client` from here and gain full multi-provider support
transparently.
"""

from app.pipeline.llm.multi_llm_router import get_llm_client

__all__ = ["get_llm_client"]
