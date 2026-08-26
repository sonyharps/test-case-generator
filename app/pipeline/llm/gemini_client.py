"""
Gemini Client for Google's fast LLM inference.

Gemini 2.0 Flash provides fast inference with generous free tier:
- 1,500 requests/day
- 250,000 TPM (tokens per minute)
- 15 RPM (requests per minute)

Get your API key at: https://aistudio.google.com/apikey
"""

import os
import asyncio
import httpx
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Rate limiting: Gemini free tier has limits but they're generous
# Add small delay between requests to be safe
GEMINI_REQUEST_DELAY = 0.5  # seconds between requests
last_gemini_request_time = 0


async def _rate_limit_delay():
    """Add small delay between Gemini requests"""
    global last_gemini_request_time
    import time

    if last_gemini_request_time > 0:
        elapsed = time.time() - last_gemini_request_time
        if elapsed < GEMINI_REQUEST_DELAY:
            wait_time = GEMINI_REQUEST_DELAY - elapsed
            await asyncio.sleep(wait_time)

    last_gemini_request_time = time.time()


class GeminiClient:
    """Client for Google Gemini API (2.0 Flash)"""

    # Configurable generation defaults (overridable per-call via generate() kwargs)
    DEFAULT_MAX_TOKENS = 8192   # was 2048 (hardcoded) — bumped for multi-TC generation
    DEFAULT_TEMPERATURE = 0.4   # was 0.2 — higher diversity for richer test scenarios

    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model
        self.api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Please set the GEMINI_API_KEY environment variable. "
                "Get your API key at: https://aistudio.google.com/apikey"
            )

        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    async def generate(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate completion from Gemini API with retry on rate limit.

        Args:
            prompt: The input prompt.
            max_tokens: Override default max output tokens (default 8192).
            temperature: Override default sampling temperature (default 0.4).
        """
        max_retries = 3
        base_delay = 3.0  # seconds

        # Resolve per-call overrides against class defaults
        eff_max_tokens = max_tokens if max_tokens is not None else self.DEFAULT_MAX_TOKENS
        eff_temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE

        for attempt in range(max_retries):
            # Rate limit delay before request
            await _rate_limit_delay()

            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": eff_temperature,
                    "maxOutputTokens": eff_max_tokens,
                }
            }

            logger.info(
                "gemini_api_request",
                model=self.model,
                prompt_length=len(prompt),
                attempt=attempt + 1,
            )

            timeout = httpx.Timeout(60.0, connect=10.0)

            try:
                async with httpx.AsyncClient(timeout=timeout, verify=True) as client:
                    # Use X-goog-api-key header
                    headers = {
                        "Content-Type": "application/json",
                        "X-goog-api-key": self.api_key,
                    }
                    logger.debug(
                        "gemini_request_details",
                        endpoint=self.endpoint,
                        api_key_prefix=self.api_key[:10] + "...",
                        headers=headers,
                    )
                    res = await client.post(self.endpoint, json=payload, headers=headers)

                    if res.status_code == 401:
                        raise RuntimeError(
                            "Gemini API authentication failed (401). Please check your GEMINI_API_KEY. "
                            "Get your API key at: https://aistudio.google.com/apikey"
                        )
                    elif res.status_code == 429:
                        error_data = res.json()
                        logger.warning("gemini_rate_limit", response=error_data)
                        if attempt < max_retries - 1:
                            # Check for retry delay in response
                            retry_delay = base_delay * (2 ** attempt)
                            if "details" in error_data.get("error", {}):
                                for detail in error_data["error"].get("details", []):
                                    if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                                        retry_delay = int(detail.get("retryDelay", "60s").replace("s", ""))

                            logger.warning(
                                "gemini_rate_limit_retry",
                                attempt=attempt + 1,
                                delay_seconds=retry_delay,
                            )
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            raise RuntimeError(
                                f"Gemini API quota exceeded. Your free tier may be: "
                                f"1) Not available in your region, 2) Requires billing setup, or 3) Exhausted. "
                                f"Enable billing at console.cloud.google.com for free tier. "
                                f"Use Groq or Local provider instead."
                            )
                    elif res.status_code == 400:
                        error_data = res.json()
                        raise RuntimeError(
                            f"Gemini API bad request (400): {error_data}"
                        )
                    elif res.status_code != 200:
                        raise RuntimeError(
                            f"Gemini API error ({res.status_code}): {res.text[:200]}"
                        )

                    data = res.json()

                    # Extract content from Gemini response
                    try:
                        content = data["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError) as e:
                        raise RuntimeError(
                            f"Unexpected Gemini API response format: {data}"
                        ) from e

                    logger.info(
                        "gemini_api_success",
                        model=self.model,
                        status_code=res.status_code,
                        response_length=len(content)
                    )

                    return content

            except httpx.ConnectTimeout as e:
                logger.error("gemini_timeout", error=str(e))
                raise RuntimeError(
                    "Gemini API connection timeout. Check your internet connection."
                ) from e

            except httpx.ConnectError as e:
                logger.error("gemini_connect_error", error=str(e))
                raise RuntimeError(
                    "Gemini API connection failed. This may be a network issue or the API is down."
                ) from e

            except httpx.TimeoutException as e:
                logger.error("gemini_timeout_exception", error=str(e))
                raise RuntimeError(
                    "Gemini API request timed out. Server took too long to respond."
                ) from e

            except httpx.RequestError as e:
                logger.error("gemini_request_error", error_type=type(e).__name__, error=str(e))
                raise RuntimeError(
                    f"Gemini API request failed ({type(e).__name__}): {str(e) or 'Unknown error'}"
                ) from e

        raise RuntimeError("Max retries exceeded for Gemini API")
