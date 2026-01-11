"""
LLM Management API

Endpoints for managing and querying LLM providers and models.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from app.core.config import settings
from app.core.logging_config import get_logger
import aiohttp
import asyncio

logger = get_logger(__name__)

router = APIRouter()


# Available model configurations
AVAILABLE_MODELS = {
    "ollama": {
        "provider": "ollama",
        "type": "local",
        "models": [
            {"id": "llama3.1:8b", "name": "Llama 3.1 8B", "description": "General purpose, fast"},
            {"id": "llama3.1:70b", "name": "Llama 3.1 70B", "description": "High quality, slower"},
            {"id": "llama3.2:3b", "name": "Llama 3.2 3B", "description": "Lightweight, very fast"},
            {"id": "mistral:7b", "name": "Mistral 7B", "description": "Good balance"},
            {"id": "phi3:latest", "name": "Phi 3", "description": "Compact, efficient"},
            {"id": "gemma2:9b", "name": "Gemma 2 9B", "description": "Google model"},
            {"id": "qwen2.5:7b", "name": "Qwen 2.5 7B", "description": "Alibaba model"},
        ]
    },
    "glm": {
        "provider": "glm",
        "type": "api",
        "models": [
            {"id": "glm-4.5-flash", "name": "GLM-4.5 Flash", "description": "Fast, efficient model"},
            {"id": "glm-4-flash", "name": "GLM-4 Flash", "description": "Alternative flash model"},
        ]
    }
}


async def check_ollama_health() -> Dict[str, Any]:
    """Check if Ollama is running and list available models"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{settings.OLLAMA_URL}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return {
                        "status": "healthy",
                        "url": settings.OLLAMA_URL,
                        "available_models": models
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "url": settings.OLLAMA_URL,
                        "error": f"HTTP {resp.status}"
                    }
    except Exception as e:
        return {
            "status": "unreachable",
            "url": settings.OLLAMA_URL,
            "error": str(e)
        }


async def check_glm_health() -> Dict[str, Any]:
    """Check if GLM API is accessible"""
    if not settings.GLM_API_KEY:
        return {
            "status": "not_configured",
            "error": "GLM_API_KEY not set"
        }

    try:
        async with aiohttp.ClientSession() as session:
            # Try a simple API call to verify the key works
            async with session.post(
                "https://api.z.ai/api/paas/v4/chat/completions",
                json={
                    "model": "glm-4.5-flash",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1
                },
                headers={"Authorization": f"Bearer {settings.GLM_API_KEY}"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status in [200, 201]:
                    return {"status": "healthy"}
                elif resp.status == 401:
                    return {"status": "unauthorized", "error": "Invalid API key"}
                else:
                    text = await resp.text()
                    return {"status": "error", "error": f"HTTP {resp.status}: {text[:100]}"}
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}


@router.get("/models")
async def list_models(current_user: User = Depends(get_current_active_user)):
    """
    List all available LLM models by provider.

    Returns configured models for both Ollama (local) and GLM (API).
    """
    return AVAILABLE_MODELS


@router.get("/health")
async def health_check(current_user: User = Depends(get_current_active_user)):
    """
    Check health status of all LLM providers.

    Returns connection status and available models for each provider.
    """
    ollama_health, glm_health = await asyncio.gather(
        check_ollama_health(),
        check_glm_health()
    )

    return {
        "ollama": ollama_health,
        "glm": glm_health,
        "timestamp": "now"
    }


@router.post("/test")
async def test_model(
    model: str = "llama3.1:8b",
    current_user: User = Depends(get_current_active_user)
):
    """
    Quick test endpoint to verify a model works.

    Simple test without full orchestrator overhead.
    """
    from app.pipeline.llm.client_ollama import OllamaClient
    import time

    start_time = time.time()

    try:
        client = OllamaClient(model)
        result = await client.generate("Say 'Hello World' in one sentence.")

        elapsed = time.time() - start_time

        return {
            "status": "success",
            "model": model,
            "response": result,
            "time_seconds": round(elapsed, 2)
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "status": "error",
            "model": model,
            "error": str(e),
            "time_seconds": round(elapsed, 2)
        }


@router.get("/providers")
async def list_providers(current_user: User = Depends(get_current_active_user)):
    """
    List available LLM providers with their configuration status.
    """
    return {
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama",
                "type": "local",
                "configured": True,
                "url": settings.OLLAMA_URL,
                "description": "Local LLM server"
            },
            {
                "id": "glm",
                "name": "GLM (Zhipu AI)",
                "type": "api",
                "configured": bool(settings.GLM_API_KEY),
                "description": "GLM-4 series models",
                "api_key_set": bool(settings.GLM_API_KEY)
            }
        ]
    }


@router.get("/config")
async def get_config(current_user: User = Depends(get_current_active_user)):
    """
    Get current LLM configuration (without sensitive data).
    """
    return {
        "ollama_url": settings.OLLAMA_URL,
        "glm_configured": bool(settings.GLM_API_KEY),
        "available_strategies": ["single", "ensemble", "cascade"],
        "available_providers": ["ollama", "glm"]
    }
