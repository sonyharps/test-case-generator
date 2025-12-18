import requests
import json
from typing import Optional


OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"


def call_llm(prompt: str, model: str = "llama3.1:8b", temperature: float = 0.2) -> str:
    """
    Wrapper universal untuk memanggil LLM dari Ollama.
    Return: murni text dari LLM.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }

    try:
        response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=180)
        response.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"LLM request error: {e}")

    data = response.json()

    # Ollama returns {"response": "..."}
    return data.get("response", "").strip()
