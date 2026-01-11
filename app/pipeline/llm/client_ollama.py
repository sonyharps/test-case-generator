# app/pipeline/llm/client_ollama.py

import aiohttp
import asyncio
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class OllamaClient:
    def __init__(self, model: str):
        self.model = model
        self.url = f"{settings.OLLAMA_URL}/api/generate"

    async def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "num_predict": 1024,   # Reduced for faster response
            "options": {
                "num_ctx": 4096,    # Context window
                "temperature": 0.2   # Lower temp for faster deterministic output
            }
        }

        logger.info(
            "ollama_request",
            model=self.model,
            url=self.url,
            prompt_length=len(prompt)
        )

        start_time = asyncio.get_event_loop().time()

        try:
            # Use ClientTimeout with separate connect and total timeouts
            timeout = aiohttp.ClientTimeout(
                total=None,     # No total timeout (let sock_read control)
                connect=60,     # 60 seconds to connect
                sock_read=600   # 10 minutes per read operation
            )

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.url, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(
                            "ollama_http_error",
                            status=resp.status,
                            error=error_text[:500]
                        )
                        raise RuntimeError(f"Ollama error {resp.status}: {error_text}")

                    data = await resp.json()

                    # Ollama sometimes uses `response`, sometimes `message`
                    raw = data.get("response") or data.get("message") or ""

                    elapsed = asyncio.get_event_loop().time() - start_time

                    logger.info(
                        "ollama_success",
                        model=self.model,
                        response_length=len(raw),
                        time_seconds=int(elapsed)
                    )

                    # safety cleanup
                    return raw.strip()

        except asyncio.TimeoutError as e:
            logger.error(
                "ollama_timeout",
                model=self.model,
                error=str(e)
            )
            raise RuntimeError(
                f"Ollama request timeout for model '{self.model}'. "
                f"The model may still be loading. Try again in a moment."
            ) from e

        except aiohttp.ClientError as e:
            logger.error(
                "ollama_connection_error",
                model=self.model,
                error=str(e)
            )
            raise RuntimeError(
                f"Cannot connect to Ollama at {settings.OLLAMA_URL}. "
                f"Make sure Ollama is running with 'ollama serve'"
            ) from e

        except Exception as e:
            logger.error(
                "ollama_error",
                model=self.model,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
