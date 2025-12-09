import requests
from app.core.config import settings

def ollama_generate(model: str, prompt: str):
    url = f"{settings.OLLAMA_URL}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        raise Exception(f"Ollama error: {response.text}")

    return response.json().get("response", "")
