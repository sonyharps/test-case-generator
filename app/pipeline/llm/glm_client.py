"""
GLM Client for GLM-4 series models from Zhipu AI.

Requires GLM_API_KEY environment variable.
Get your API key at: https://open.bigmodel.cn/
"""

import os
import httpx
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class GLMClient:
    """Client for GLM (Zhipu AI) API models"""

    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("GLM_API_KEY") or settings.GLM_API_KEY

        if not self.api_key:
            raise RuntimeError(
                "GLM_API_KEY is not set. Please set the GLM_API_KEY environment variable, "
                "or use Ollama models instead. Get your API key at: https://open.bigmodel.cn/"
            )

        self.endpoint = "https://api.z.ai/api/paas/v4/chat/completions"

    async def generate(self, prompt: str) -> str:
        """Generate completion from GLM API"""
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

        # Configure timeout and limits
        # GLM API can be slow, use 5 minute timeout
        timeout = httpx.Timeout(300.0, connect=60.0)
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

        logger.info(
            "glm_api_request",
            model=self.model,
            endpoint=self.endpoint,
            prompt_length=len(prompt)
        )

        async with httpx.AsyncClient(timeout=timeout, limits=limits, verify=True) as client:
            try:
                res = await client.post(self.endpoint, json=payload, headers=headers)
                res.raise_for_status()

                data = res.json()
                content = data["choices"][0]["message"]["content"]

                logger.info(
                    "glm_api_success",
                    model=self.model,
                    status_code=res.status_code,
                    response_length=len(content)
                )

                return content

            except httpx.HTTPStatusError as e:
                logger.error(
                    "glm_api_http_error",
                    status_code=e.response.status_code,
                    response_text=e.response.text[:500],
                    model=self.model
                )
                if e.response.status_code == 401:
                    raise RuntimeError(
                        "GLM API authentication failed (401). Please check your GLM_API_KEY. "
                        "Get your API key at: https://open.bigmodel.cn/"
                    ) from e
                elif e.response.status_code == 429:
                    raise RuntimeError(
                        f"GLM API rate limit exceeded (429): {e.response.text[:200]}"
                    ) from e
                else:
                    raise RuntimeError(
                        f"GLM API error ({e.response.status_code}): {e.response.text[:200]}"
                    ) from e

            except httpx.ConnectTimeout as e:
                logger.error("glm_api_timeout", error=str(e), endpoint=self.endpoint)
                raise RuntimeError(
                    f"GLM API connection timeout. Cannot reach {self.endpoint}. "
                    "Check your internet connection or try Local LLM mode instead."
                ) from e

            except httpx.ConnectError as e:
                logger.error("glm_api_connect_error", error=str(e), endpoint=self.endpoint)
                raise RuntimeError(
                    f"GLM API connection failed. Cannot reach {self.endpoint}. "
                    "This may be a network issue, firewall, or the API is down. "
                    "Try using Local LLM mode instead."
                ) from e

            except httpx.TimeoutException as e:
                logger.error("glm_api_timeout_exception", error=str(e))
                raise RuntimeError(
                    f"GLM API request timed out. Server took too long to respond. "
                    "Try using Local LLM mode for faster results."
                ) from e

            except httpx.RequestError as e:
                logger.error("glm_api_request_error", error_type=type(e).__name__, error=str(e))
                raise RuntimeError(
                    f"GLM API request failed ({type(e).__name__}): {str(e) or 'Unknown error'}. "
                    "Try using Local LLM mode instead."
                ) from e
