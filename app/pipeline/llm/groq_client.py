"""
Groq Client for fast cloud LLM inference.

Groq provides ultra-fast inference for open models like Llama, Mixtral, etc.
Get your API key at: https://console.groq.com/keys
Free tier: 8M tokens/day, 6000 TPM (tokens per minute)
"""

import os
import asyncio
import httpx
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Rate limiting: Groq free tier has 6000 TPM limit
# Add delay between requests to avoid hitting rate limit
GROQ_REQUEST_DELAY = 2.0  # seconds between requests
last_groq_request_time = 0


async def _rate_limit_delay():
    """Add delay between Groq requests to avoid rate limiting"""
    global last_groq_request_time
    import time

    if last_groq_request_time > 0:
        elapsed = time.time() - last_groq_request_time
        if elapsed < GROQ_REQUEST_DELAY:
            wait_time = GROQ_REQUEST_DELAY - elapsed
            logger.info("groq_rate_limit_wait", wait_seconds=wait_time)
            await asyncio.sleep(wait_time)

    last_groq_request_time = time.time()


class GroqClient:
    """Client for Groq API (ultra-fast inference)"""

    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY

        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Please set the GROQ_API_KEY environment variable. "
                "Get your API key at: https://console.groq.com/keys"
            )

        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    async def generate(self, prompt: str) -> str:
        """Generate completion from Groq API with retry on rate limit"""
        max_retries = 3
        base_delay = 5.0  # seconds

        for attempt in range(max_retries):
            # Rate limit delay before request
            await _rate_limit_delay()

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
                "max_tokens": 2048,
            }

            logger.info(
                "groq_api_request",
                model=self.model,
                endpoint=self.endpoint,
                prompt_length=len(prompt),
                attempt=attempt + 1,
            )

            # Groq is very fast, but set reasonable timeout
            timeout = httpx.Timeout(60.0, connect=10.0)

            try:
                async with httpx.AsyncClient(timeout=timeout, verify=True) as client:
                    res = await client.post(self.endpoint, json=payload, headers=headers)

                    if res.status_code == 401:
                        raise RuntimeError(
                            "Groq API authentication failed (401). Please check your GROQ_API_KEY. "
                            "Get your API key at: https://console.groq.com/keys"
                        )
                    elif res.status_code == 429:
                        if attempt < max_retries - 1:
                            # Exponential backoff for rate limit
                            delay = base_delay * (2 ** attempt)
                            logger.warning(
                                "groq_rate_limit_retry",
                                attempt=attempt + 1,
                                delay_seconds=delay,
                                response=res.text[:200]
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            raise RuntimeError(
                                f"Groq API rate limit exceeded after {max_retries} retries. "
                                f"Free tier has 6000 TPM limit. Try: 1) Wait a minute, "
                                f"2) Use Local provider (Ollama), or 3) Upgrade Groq plan."
                            )
                    elif res.status_code != 200:
                        raise RuntimeError(
                            f"Groq API error ({res.status_code}): {res.text[:200]}"
                        )

                    res.raise_for_status()
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]

                    logger.info(
                        "groq_api_success",
                        model=self.model,
                        status_code=res.status_code,
                        response_length=len(content)
                    )

                    return content

            except httpx.ConnectTimeout as e:
                logger.error("groq_timeout", error=str(e), endpoint=self.endpoint)
                raise RuntimeError(
                    f"Groq API connection timeout. Cannot reach {self.endpoint}. "
                    "Check your internet connection."
                ) from e

            except httpx.ConnectError as e:
                logger.error("groq_connect_error", error=str(e), endpoint=self.endpoint)
                raise RuntimeError(
                    f"Groq API connection failed. Cannot reach {self.endpoint}. "
                    "This may be a network issue or the API is down."
                ) from e

            except httpx.TimeoutException as e:
                logger.error("groq_timeout_exception", error=str(e))
                raise RuntimeError(
                    f"Groq API request timed out. Server took too long to respond."
                ) from e

            except httpx.RequestError as e:
                logger.error("groq_request_error", error_type=type(e).__name__, error=str(e))
                raise RuntimeError(
                    f"Groq API request failed ({type(e).__name__}): {str(e) or 'Unknown error'}"
                ) from e

        raise RuntimeError("Max retries exceeded for Groq API")
