"""
OpenRouter Client — unified access to many LLM vendors via openrouter.ai.

OpenRouter is OpenAI-compatible: any model is addressed as "vendor/model"
(e.g. "deepseek/deepseek-chat", "google/gemini-2.5-flash"). Requires the
OPENROUTER_API_KEY environment variable (https://openrouter.ai/keys).
"""

import os
import httpx
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class OpenRouterClient:
    """Client for LLM models served through OpenRouter."""

    DEFAULT_MAX_TOKENS = 16384
    DEFAULT_TEMPERATURE = 0.4

    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("OPENROUTER_API_KEY") or settings.OPENROUTER_API_KEY

        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Please set the OPENROUTER_API_KEY "
                "environment variable. Get your key at: https://openrouter.ai/keys"
            )

        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"

    async def generate(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate completion via OpenRouter.

        Args:
            prompt: The input prompt.
            max_tokens: Override default max output tokens.
            temperature: Override default sampling temperature.
        """
        eff_max_tokens = max_tokens if max_tokens is not None else self.DEFAULT_MAX_TOKENS
        eff_temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Optional OpenRouter attribution headers
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "QA Test Case Generator",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": eff_temperature,
            "max_tokens": eff_max_tokens,
        }

        # High-volume generation (100+ TCs at 65k budget) can take a while.
        timeout = httpx.Timeout(900.0, connect=60.0)
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

        logger.info(
            "openrouter_api_request",
            model=self.model,
            prompt_length=len(prompt),
        )

        async with httpx.AsyncClient(timeout=timeout, limits=limits, verify=True) as client:
            try:
                res = await client.post(self.endpoint, json=payload, headers=headers)
                res.raise_for_status()

                data = res.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content") or ""

                # Some reasoning models expose a separate reasoning field;
                # only use it as a fallback when the final content is empty.
                if not content.strip():
                    content = msg.get("reasoning") or ""

                logger.info(
                    "openrouter_api_success",
                    model=self.model,
                    status_code=res.status_code,
                    response_length=len(content),
                )
                return content

            except httpx.HTTPStatusError as e:
                body = e.response.text[:300]
                logger.error(
                    "openrouter_http_error",
                    status_code=e.response.status_code,
                    response_text=body,
                    model=self.model,
                )
                if e.response.status_code == 401:
                    raise RuntimeError(
                        "OpenRouter authentication failed (401). Check OPENROUTER_API_KEY."
                    ) from e
                elif e.response.status_code == 402:
                    raise RuntimeError(
                        f"OpenRouter insufficient credits (402): {body}"
                    ) from e
                elif e.response.status_code == 429:
                    raise RuntimeError(
                        f"OpenRouter rate limit (429): {body}"
                    ) from e
                raise RuntimeError(
                    f"OpenRouter API error ({e.response.status_code}): {body}"
                ) from e

            except httpx.TimeoutException as e:
                logger.error("openrouter_timeout", model=self.model, error=str(e))
                raise RuntimeError(
                    "OpenRouter request timed out. The model took too long to respond."
                ) from e

            except httpx.RequestError as e:
                logger.error(
                    "openrouter_request_error",
                    error_type=type(e).__name__,
                    error=str(e),
                )
                raise RuntimeError(
                    f"OpenRouter request failed ({type(e).__name__}): {e}"
                ) from e
