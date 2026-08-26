# app/pipeline/llm/multi_llm_router.py
"""
Enhanced Multi-LLM Router supporting:
- Simple preset modes (local_only, glm_only, combined)
- Single model selection
- Ensemble (combine multiple model outputs)
- Cascade (fallback on failure)

Supported Providers:
- OLLAMA: Local models (llama3.1, mistral, phi, etc.)
- GLM: GLM API (glm-4-plus, glm-4-flash, etc.)
- GROQ: Fast cloud inference (llama-3.1-8b, mixtral, etc.)
- GEMINI: Google Gemini 2.0 Flash (generous free tier)
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Union
from app.schemas.llm_schema import (
    LLMConfiguration, LLMResult, EnsembleResult, LLMProvider,
    MultiLLMStrategy, LLMMode, ModelConfig
)
from app.pipeline.llm.client_ollama import OllamaClient
from app.pipeline.llm.glm_client import GLMClient
from app.pipeline.llm.groq_client import GroqClient
from app.pipeline.llm.openrouter_client import OpenRouterClient
from app.pipeline.llm.gemini_client import GeminiClient
from app.core.logging_config import get_logger
from app.core.config import settings

logger = get_logger(__name__)

# =====================================================
# GLM API RATE LIMITING
# =====================================================
# GLM API has very strict concurrency limits (error 1302)
# Concurrency control for GLM API.
# Semaphore-based: allows up to GLM_MAX_CONCURRENT in-flight requests while
# enforcing a minimum interval between request STARTS. This lets the V8
# parallel-category pipeline (3 concurrent calls) run truly in parallel,
# instead of the old single-worker queue which fully serialized requests.
GLM_MAX_CONCURRENT = 3
GLM_MIN_INTERVAL = 1.0  # seconds between request starts

_glm_semaphore: asyncio.Semaphore = None
_glm_last_start_time: float = 0.0
_glm_interval_lock: asyncio.Lock = None


def _ensure_glm_limiter():
    """Lazily initialize the semaphore + interval lock (once per process)."""
    global _glm_semaphore, _glm_interval_lock
    if _glm_semaphore is None:
        _glm_semaphore = asyncio.Semaphore(GLM_MAX_CONCURRENT)
    if _glm_interval_lock is None:
        _glm_interval_lock = asyncio.Lock()


async def rate_limited_glm_generate(
    client: GLMClient,
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> str:
    """
    Generate with GLM API with bounded concurrency.

    Up to GLM_MAX_CONCURRENT requests run in parallel; each request start
    is staggered by at least GLM_MIN_INTERVAL seconds to stay under the
    Z.AI concurrency/rate limits.
    """
    global _glm_last_start_time

    _ensure_glm_limiter()

    # Build generation kwargs (drop None values so client defaults apply)
    gen_kwargs = {}
    if max_tokens is not None:
        gen_kwargs["max_tokens"] = max_tokens
    if temperature is not None:
        gen_kwargs["temperature"] = temperature

    async with _glm_semaphore:
        # Stagger request starts to smooth burst concurrency
        async with _glm_interval_lock:
            elapsed = time.time() - _glm_last_start_time
            if elapsed < GLM_MIN_INTERVAL:
                wait = GLM_MIN_INTERVAL - elapsed
                logger.info("glm_rate_limit_wait", wait_seconds=wait)
                await asyncio.sleep(wait)
            _glm_last_start_time = time.time()

        try:
            result = await client.generate(prompt, **gen_kwargs)
            return result
        except Exception as e:
            # If we get a 429 (rate limit), the API is still limiting us
            if "1302" in str(e) or "429" in str(e) or "concurrency" in str(e).lower():
                logger.error(
                    "glm_rate_limit_still_hit",
                    error=str(e),
                    note="GLM API concurrency limit hit."
                )
                raise RuntimeError(
                    "GLM API rate limit exceeded. The Z.AI API has very strict rate limits. "
                    "Please retry, or contact Z.AI to increase your limits."
                ) from e
            raise


class MultiLLMRouter:
    """
    Enhanced router that supports multiple LLM providers and strategies.

    Strategies:
    - SINGLE: Use primary model only
    - ENSEMBLE: Run multiple models and merge results
    - CASCADE: Try primary, fallback to secondary on failure
    """

    def __init__(self, config: Union[LLMConfiguration, str, None]):
        """
        Initialize router with configuration.

        Args:
            config: Can be:
                - LLMConfiguration object with simple mode (local_only, glm_only, combined)
                - LLMConfiguration object with full multi-LLM config
                - String model name (backward compatible, uses SINGLE strategy)
                - None (uses the configured DEFAULT_LLM_MODEL)
        """
        if config is None:
            config = settings.DEFAULT_LLM_MODEL

        if isinstance(config, str):
            # Backward compatible: simple model string
            self.config = self._create_config_from_string(config)
        elif isinstance(config, LLMConfiguration):
            # Process simple mode if set, otherwise use as-is
            self.config = self._resolve_config(config)
        else:
            raise ValueError(f"Invalid config type: {type(config)}")

        # Cache for clients
        self._clients: Dict[tuple, Any] = {}

    def _create_config_from_string(self, model: str) -> LLMConfiguration:
        """Create LLMConfiguration from simple model string (backward compatibility)"""
        provider = self._detect_provider(model)
        from app.schemas.llm_schema import ModelConfig
        return LLMConfiguration(
            strategy=MultiLLMStrategy.SINGLE,
            primary=ModelConfig(provider=provider, model=model)
        )

    def _resolve_config(self, config: LLMConfiguration) -> LLMConfiguration:
        """
        Resolve simple mode to full configuration.

        Converts simple mode (local_only, glm_only, combined) to full
        LLMConfiguration with strategy, primary, and secondary models.
        """
        # If simple mode is set, convert to full config
        if config.mode:
            return self._mode_to_config(config)

        # If advanced config is provided, ensure it's complete
        if config.strategy and config.primary:
            return config

        # Default: local only
        return LLMConfiguration(
            strategy=MultiLLMStrategy.SINGLE,
            primary=ModelConfig(provider=LLMProvider.OLLAMA, model=config.local_model)
        )

    def _mode_to_config(self, config: LLMConfiguration) -> LLMConfiguration:
        """Convert simple mode to full LLMConfiguration"""
        mode = config.mode

        if mode == LLMMode.LOCAL_ONLY:
            # Use only Ollama (local)
            return LLMConfiguration(
                strategy=MultiLLMStrategy.SINGLE,
                primary=ModelConfig(provider=LLMProvider.OLLAMA, model=config.local_model),
                local_model=config.local_model,
                glm_model=config.glm_model,
                models_by_type=config.models_by_type
            )

        elif mode == LLMMode.GLM_ONLY:
            # Use only GLM API
            return LLMConfiguration(
                strategy=MultiLLMStrategy.SINGLE,
                primary=ModelConfig(provider=LLMProvider.GLM, model=config.glm_model),
                local_model=config.local_model,
                glm_model=config.glm_model,
                models_by_type=config.models_by_type
            )

        elif mode == LLMMode.COMBINED:
            # Combine both in ensemble mode
            return LLMConfiguration(
                strategy=MultiLLMStrategy.ENSEMBLE,
                primary=ModelConfig(
                    provider=LLMProvider.OLLAMA,
                    model=config.local_model,
                    weight=config.local_weight
                ),
                secondary=[
                    ModelConfig(
                        provider=LLMProvider.GLM,
                        model=config.glm_model,
                        weight=config.glm_weight
                    )
                ],
                merge_method=config.merge_method,
                local_model=config.local_model,
                glm_model=config.glm_model,
                models_by_type=config.models_by_type
            )

        # Fallback to local only
        return LLMConfiguration(
            strategy=MultiLLMStrategy.SINGLE,
            primary=ModelConfig(provider=LLMProvider.OLLAMA, model=config.local_model)
        )

    def _detect_provider(self, model: str) -> LLMProvider:
        """Auto-detect provider from model name"""
        model_lower = model.lower()

        # OpenRouter models are addressed as "vendor/model" (e.g.
        # "deepseek/deepseek-chat"). Detect that prefix first so vendor
        # names like "google/gemini-..." or "meta-llama/..." route to
        # OpenRouter instead of the direct-provider clients.
        if model_lower.startswith("openrouter/"):
            return LLMProvider.OPENROUTER
        if "/" in model_lower and any(
            model_lower.startswith(v)
            for v in ("deepseek/", "qwen/", "openai/", "anthropic/", "meta-llama/",
                      "mistralai/", "google/", "x-ai/", "moonshotai/")
        ):
            return LLMProvider.OPENROUTER

        if any(key in model_lower for key in ["gemini", "google"]):
            return LLMProvider.GEMINI
        elif any(key in model_lower for key in ["groq", "llama-3", "mixtral", "gemma"]):
            return LLMProvider.GROQ
        elif any(key in model_lower for key in ["glm", "chatglm"]):
            return LLMProvider.GLM
        else:
            return LLMProvider.OLLAMA

    def _get_client(self, provider: LLMProvider, model: str):
        """Get or create client for provider/model combination"""
        cache_key = (provider, model)

        if cache_key not in self._clients:
            if provider == LLMProvider.OLLAMA:
                self._clients[cache_key] = OllamaClient(model)
            elif provider == LLMProvider.GLM:
                self._clients[cache_key] = GLMClient(model)
            elif provider == LLMProvider.GROQ:
                self._clients[cache_key] = GroqClient(model)
            elif provider == LLMProvider.GEMINI:
                self._clients[cache_key] = GeminiClient(model)
            elif provider == LLMProvider.OPENROUTER:
                # Allow "openrouter/vendor/model" — strip the prefix.
                eff_model = model[len("openrouter/"):] if model.lower().startswith("openrouter/") else model
                self._clients[cache_key] = OpenRouterClient(eff_model)
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        return self._clients[cache_key]

    async def generate(
        self,
        prompt: str,
        test_type: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate content using configured strategy.

        Args:
            prompt: The prompt to send to the LLM
            test_type: Optional test type (functional, negative, boundary)
                      for model-specific overrides
            max_tokens: Optional override for max output tokens (None = client default)
            temperature: Optional override for sampling temperature (None = client default)

        Returns:
            Generated content as string
        """
        # Check for per-type model override
        if test_type and self.config.models_by_type and test_type in self.config.models_by_type:
            override_config = self.config.models_by_type[test_type]
            single_config = LLMConfiguration(
                strategy=MultiLLMStrategy.SINGLE,
                primary=override_config
            )
            override_router = MultiLLMRouter(single_config)
            return await override_router.generate(
                prompt, max_tokens=max_tokens, temperature=temperature
            )

        gen_kwargs = {"max_tokens": max_tokens, "temperature": temperature}

        if self.config.strategy == MultiLLMStrategy.SINGLE:
            return await self._generate_single(prompt, **gen_kwargs)

        elif self.config.strategy == MultiLLMStrategy.ENSEMBLE:
            result = await self._generate_ensemble(prompt, **gen_kwargs)
            return result.merged_content

        elif self.config.strategy == MultiLLMStrategy.CASCADE:
            return await self._generate_cascade(prompt, **gen_kwargs)

        else:
            raise ValueError(f"Unknown strategy: {self.config.strategy}")

    async def _generate_single(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate using primary model only"""
        client = self._get_client(self.config.primary.provider, self.config.primary.model)

        start_time = time.time()
        # Use rate-limited generation for GLM API to avoid concurrency errors
        if self.config.primary.provider == LLMProvider.GLM and isinstance(client, GLMClient):
            content = await rate_limited_glm_generate(
                client, prompt, max_tokens=max_tokens, temperature=temperature
            )
        else:
            content = await client.generate(
                prompt, max_tokens=max_tokens, temperature=temperature
            )
        elapsed_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "llm_single_generation",
            provider=self.config.primary.provider.value,
            model=self.config.primary.model,
            time_ms=elapsed_ms
        )

        return content

    async def _generate_ensemble(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> EnsembleResult:
        """
        Generate using multiple models and merge results.

        Merge methods:
        - weighted: Weighted combination based on model weights
        - majority: Use most common elements across results
        - concat: Concatenate all results
        """
        models = [self.config.primary] + self.config.secondary

        # Run all models in parallel
        tasks = []
        for model_config in models:
            client = self._get_client(model_config.provider, model_config.model)
            tasks.append(self._generate_with_metadata(
                client, model_config, prompt, max_tokens=max_tokens, temperature=temperature
            ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed results
        valid_results = [r for r in results if isinstance(r, LLMResult)]

        if not valid_results:
            raise RuntimeError("All models in ensemble failed")

        # Merge results based on method
        merged = self._merge_results(valid_results, prompt)

        logger.info(
            "llm_ensemble_generation",
            num_models=len(models),
            successful=len(valid_results),
            merge_method=self.config.merge_method
        )

        return EnsembleResult(
            merged_content=merged,
            individual_results=valid_results,
            merge_method=self.config.merge_method,
            agreement_score=self._calculate_agreement(valid_results)
        )

    async def _generate_with_metadata(
        self,
        client,
        model_config,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> LLMResult:
        """Generate with timing and metadata"""
        start_time = time.time()
        try:
            # Use rate-limited generation for GLM API to avoid concurrency errors
            if model_config.provider == LLMProvider.GLM and isinstance(client, GLMClient):
                content = await rate_limited_glm_generate(
                    client, prompt, max_tokens=max_tokens, temperature=temperature
                )
            else:
                content = await client.generate(
                    prompt, max_tokens=max_tokens, temperature=temperature
                )

            elapsed_ms = int((time.time() - start_time) * 1000)

            return LLMResult(
                content=content,
                model_used=model_config.model,
                provider=model_config.provider,
                generation_time_ms=elapsed_ms,
                is_fallback=False
            )
        except Exception as e:
            logger.warning(
                "llm_generation_failed",
                model=model_config.model,
                error=str(e)
            )
            raise

    def _merge_results(self, results: List[LLMResult], original_prompt: str) -> str:
        """Merge results from multiple models"""
        if self.config.merge_method == "concat":
            # Simple concatenation
            return "\n\n".join([r.content for r in results])

        elif self.config.merge_method == "weighted":
            # Weighted selection (use result from highest weighted model that succeeded)
            # Sort by weight descending
            models = [self.config.primary] + self.config.secondary
            model_results = list(zip(models, results))

            # Sort by weight
            model_results.sort(key=lambda x: x[0].weight, reverse=True)

            # Return content from highest weighted successful model
            for model_config, result in model_results:
                if result.content:
                    return result.content

            # Fallback to first result
            return results[0].content

        elif self.config.merge_method == "majority":
            # For JSON outputs, try to find common elements
            # For simplicity, return the most common result length
            from collections import Counter

            lengths = [len(r.content) for r in results]
            most_common_length = Counter(lengths).most_common(1)[0][0]

            # Find result closest to common length
            for r in results:
                if len(r.content) == most_common_length:
                    return r.content

            return results[0].content

        else:
            # Default: return first result
            return results[0].content

    def _calculate_agreement(self, results: List[LLMResult]) -> float:
        """Calculate agreement score between results (0-1)"""
        if len(results) <= 1:
            return 1.0

        # Simple agreement based on content similarity
        # Compare lengths as a basic metric
        lengths = [len(r.content) for r in results]
        avg_length = sum(lengths) / len(lengths)

        # Calculate variance
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)

        # Lower variance = higher agreement
        # Normalize to 0-1 (this is a simple heuristic)
        agreement = max(0, 1 - (variance / (avg_length ** 2 + 1)))

        return round(agreement, 2)

    async def _generate_cascade(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate using cascade strategy.
        Try primary first, fallback to secondary models on failure.
        """
        models = [self.config.primary] + self.config.secondary

        for i, model_config in enumerate(models):
            try:
                client = self._get_client(model_config.provider, model_config.model)

                # Add timeout for cascade
                start_time = time.time()

                # Use rate-limited generation for GLM API to avoid concurrency errors
                if model_config.provider == LLMProvider.GLM and isinstance(client, GLMClient):
                    content = await asyncio.wait_for(
                        rate_limited_glm_generate(
                            client, prompt, max_tokens=max_tokens, temperature=temperature
                        ),
                        timeout=self.config.timeout_seconds
                    )
                else:
                    content = await asyncio.wait_for(
                        client.generate(
                            prompt, max_tokens=max_tokens, temperature=temperature
                        ),
                        timeout=self.config.timeout_seconds
                    )

                elapsed_ms = int((time.time() - start_time) * 1000)

                logger.info(
                    "llm_cascade_generation",
                    provider=model_config.provider.value,
                    model=model_config.model,
                    attempt=i + 1,
                    is_fallback=(i > 0),
                    time_ms=elapsed_ms
                )

                return content

            except asyncio.TimeoutError:
                logger.warning(
                    "llm_timeout",
                    model=model_config.model,
                    timeout=self.config.timeout_seconds
                )
                continue

            except Exception as e:
                logger.warning(
                    "llm_cascade_failed",
                    model=model_config.model,
                    error=str(e)
                )
                continue

        raise RuntimeError(f"All models in cascade failed: {[m.model for m in models]}")


def get_llm_router(config: Union[LLMConfiguration, str, None] = None) -> MultiLLMRouter:
    """
    Get a configured MultiLLMRouter.

    Args:
        config: LLMConfiguration, model string, or None for default

    Returns:
        Configured MultiLLMRouter instance

    Examples:
        # Simple string (auto-detects provider from model name)
        router = get_llm_router("gemini-2.0-flash")

        # Single model with config
        router = get_llm_router(LLMConfiguration(
            strategy=MultiLLMStrategy.SINGLE,
            primary=ModelConfig(provider=LLMProvider.GEMINI, model="gemini-2.0-flash")
        ))

        # Ensemble
        router = get_llm_router(LLMConfiguration(
            strategy=MultiLLMStrategy.ENSEMBLE,
            primary=ModelConfig(provider=LLMProvider.GEMINI, model="gemini-2.0-flash", weight=0.6),
            secondary=[ModelConfig(provider=LLMProvider.GROQ, model="llama-3.3-70b-versatile", weight=0.4)],
            merge_method="weighted"
        ))
    """
    return MultiLLMRouter(config)


# Backward compatibility: keep old function working
def get_llm_client(model: str):
    """Backward compatible function - returns simple client for single model"""
    router = get_llm_router(model)

    # Return a simple client wrapper
    class SimpleClientWrapper:
        def __init__(self, router: MultiLLMRouter):
            self.router = router

        async def generate(self, prompt: str) -> str:
            return await self.router.generate(prompt)

    return SimpleClientWrapper(router)
