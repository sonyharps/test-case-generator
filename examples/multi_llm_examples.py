#!/usr/bin/env python3
"""
Multi-LLM Usage Examples

This script demonstrates how to use the multi-LLM router with different strategies.

Usage:
    python examples/multi_llm_examples.py

Environment variables required:
    - GLM_API_KEY (for GLM models)
    - Ollama running locally for local models
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.pipeline.llm.multi_llm_router import get_llm_router
from app.schemas.llm_schema import (
    LLMConfiguration,
    MultiLLMStrategy,
    LLMProvider,
    ModelConfig
)


async def example_single_model():
    """Example 1: Single model (backward compatible)"""
    print("\n" + "=" * 60)
    print("Example 1: Single Model (String)")
    print("=" * 60)

    router = get_llm_router("llama3.1:8b")
    response = await router.generate("What is 2 + 2?")
    print(f"Response: {response}")


async def example_single_model_with_config():
    """Example 2: Single model with explicit config"""
    print("\n" + "=" * 60)
    print("Example 2: Single Model (Explicit Config)")
    print("=" * 60)

    config = LLMConfiguration(
        strategy=MultiLLMStrategy.SINGLE,
        primary=ModelConfig(provider=LLMProvider.OLLAMA, model="llama3.1:8b")
    )
    router = get_llm_router(config)
    response = await router.generate("What is 3 + 3?")
    print(f"Response: {response}")


async def example_ensemble():
    """Example 3: Ensemble mode - combine multiple models"""
    print("\n" + "=" * 60)
    print("Example 3: Ensemble Mode (Weighted)")
    print("=" * 60)

    config = LLMConfiguration(
        strategy=MultiLLMStrategy.ENSEMBLE,
        primary=ModelConfig(
            provider=LLMProvider.OLLAMA,
            model="llama3.1:8b",
            weight=0.6
        ),
        secondary=[
            ModelConfig(
                provider=LLMProvider.GLM,
                model="glm-4-plus",
                weight=0.4
            )
        ],
        merge_method="weighted"
    )
    router = get_llm_router(config)
    response = await router.generate("Generate a simple test case for login form")
    print(f"Response: {response[:500]}...")


async def example_cascade():
    """Example 4: Cascade mode - fallback on failure"""
    print("\n" + "=" * 60)
    print("Example 4: Cascade Mode (Fallback)")
    print("=" * 60)

    config = LLMConfiguration(
        strategy=MultiLLMStrategy.CASCADE,
        primary=ModelConfig(provider=LLMProvider.OLLAMA, model="llama3.1:8b"),
        secondary=[
            ModelConfig(provider=LLMProvider.GLM, model="glm-4-plus")
        ],
        timeout_seconds=60
    )
    router = get_llm_router(config)
    response = await router.generate("What is 5 + 5?")
    print(f"Response: {response}")


async def example_per_type():
    """Example 5: Different models for different test types"""
    print("\n" + "=" * 60)
    print("Example 5: Per-Test-Type Model Selection")
    print("=" * 60)

    config = LLMConfiguration(
        strategy=MultiLLMStrategy.SINGLE,
        primary=ModelConfig(provider=LLMProvider.OLLAMA, model="llama3.1:8b"),
        models_by_type={
            "functional": ModelConfig(provider=LLMProvider.GLM, model="glm-4-plus"),
            "negative": ModelConfig(provider=LLMProvider.OLLAMA, model="llama3.1:8b"),
            "boundary": ModelConfig(provider=LLMProvider.GLM, model="glm-4-flash"),
        }
    )
    router = get_llm_router(config)

    # Each test type will use a different model
    for test_type in ["functional", "negative", "boundary"]:
        response = await router.generate(
            f"Generate a {test_type} test case for user registration",
            test_type=test_type
        )
        print(f"\n{test_type.upper()} (uses GLM for functional/boundary, Ollama for negative):")
        print(f"  {response[:200]}...")


async def example_glm_only():
    """Example 6: Using only GLM models"""
    print("\n" + "=" * 60)
    print("Example 6: GLM Only")
    print("=" * 60)

    # Check for API key
    if not os.getenv("GLM_API_KEY"):
        print("Skipping: GLM_API_KEY not set")
        return

    config = LLMConfiguration(
        strategy=MultiLLMStrategy.SINGLE,
        primary=ModelConfig(provider=LLMProvider.GLM, model="glm-4-plus")
    )
    router = get_llm_router(config)
    response = await router.generate("What is 7 + 7?")
    print(f"Response: {response}")


async def main():
    """Run all examples"""
    examples = [
        ("Single Model (String)", example_single_model),
        ("Single Model (Config)", example_single_model_with_config),
        ("Ensemble Mode", example_ensemble),
        ("Cascade Mode", example_cascade),
        ("Per-Type Selection", example_per_type),
        ("GLM Only", example_glm_only),
    ]

    print("\n" + "=" * 60)
    print("Multi-LLM Router Examples")
    print("=" * 60)
    print("\nMake sure Ollama is running and GLM_API_KEY is set (for GLM examples)")
    print("\nRunning examples...\n")

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\nError in {name}: {e}")

    print("\n" + "=" * 60)
    print("Examples Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
