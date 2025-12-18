# app/pipeline/llm/client_ollama.py

import aiohttp

class OllamaClient:
    def __init__(self, model: str):
        self.model = model
        self.url = "http://host.docker.internal:11434/api/generate"

    async def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json=payload, timeout=120) as resp:
                data = await resp.json()

                # Ollama sometimes uses `response`, sometimes `message`
                raw = data.get("response") or data.get("message") or ""

                # safety cleanup
                return raw.strip()
