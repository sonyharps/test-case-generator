#!/bin/bash
# Multi-LLM API Examples
# This script demonstrates how to call the orchestrator with different LLM configurations

API_URL="${API_URL:-http://localhost:8000}"
TOKEN="${TOKEN:-your_bearer_token_here}"

echo "========================================"
echo "Multi-LLM API Examples"
echo "========================================"
echo "API URL: $API_URL"
echo ""

# Example 1: Simple model string (backward compatible)
echo "1. Simple Model String (Backward Compatible)"
echo "-------------------------------------------"
curl -X POST "$API_URL/v1/orchestrator/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "User login with email and password",
    "model": "llama3.1:8b"
  }' | jq '.metadata'
echo ""

# Example 2: Single model with config
echo "2. Single Model with Config"
echo "----------------------------"
curl -X POST "$API_URL/v1/orchestrator/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "User login with email and password",
    "llm_config": {
      "strategy": "single",
      "primary": {
        "provider": "ollama",
        "model": "llama3.1:8b"
      }
    }
  }' | jq '.metadata'
echo ""

# Example 3: Ensemble mode (Ollama + GLM)
echo "3. Ensemble Mode (Combine Ollama + GLM)"
echo "---------------------------------------"
curl -X POST "$API_URL/v1/orchestrator/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "User login with email and password",
    "llm_config": {
      "strategy": "ensemble",
      "primary": {
        "provider": "ollama",
        "model": "llama3.1:8b",
        "weight": 0.6
      },
      "secondary": [
        {
          "provider": "glm",
          "model": "glm-4-plus",
          "weight": 0.4
        }
      ],
      "merge_method": "weighted"
    }
  }' | jq '.metadata'
echo ""

# Example 4: Cascade mode (fallback)
echo "4. Cascade Mode (Fallback on Failure)"
echo "--------------------------------------"
curl -X POST "$API_URL/v1/orchestrator/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "User login with email and password",
    "llm_config": {
      "strategy": "cascade",
      "primary": {
        "provider": "ollama",
        "model": "llama3.1:8b"
      },
      "secondary": [
        {
          "provider": "glm",
          "model": "glm-4-plus"
        }
      ],
      "timeout_seconds": 120
    }
  }' | jq '.metadata'
echo ""

# Example 5: Per-test-type model selection
echo "5. Per-Test-Type Model Selection"
echo "--------------------------------"
curl -X POST "$API_URL/v1/orchestrator/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "User login with email and password",
    "llm_config": {
      "strategy": "single",
      "primary": {
        "provider": "ollama",
        "model": "llama3.1:8b"
      },
      "models_by_type": {
        "functional": {
          "provider": "glm",
          "model": "glm-4-plus"
        },
        "negative": {
          "provider": "ollama",
          "model": "llama3.1:8b"
        },
        "boundary": {
          "provider": "glm",
          "model": "glm-4-flash"
        }
      }
    }
  }' | jq '.metadata'
echo ""

# Example 6: GLM only
echo "6. GLM Only"
echo "------------"
curl -X POST "$API_URL/v1/orchestrator/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "User login with email and password",
    "llm_config": {
      "strategy": "single",
      "primary": {
        "provider": "glm",
        "model": "glm-4-plus"
      }
    }
  }' | jq '.metadata'
echo ""

echo "========================================"
echo "Examples Complete!"
echo "========================================"
