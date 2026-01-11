import httpx
import os


class GLMClient:
    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("GLM_API_KEY")

        if not self.api_key:
            raise RuntimeError("GLM_API_KEY is not set")

        self.endpoint = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    async def generate(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            res = await client.post(self.endpoint, json=payload, headers=headers)
            res.raise_for_status()

            data = res.json()
            return data["choices"][0]["message"]["content"]
