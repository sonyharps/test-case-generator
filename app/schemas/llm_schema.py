# app/schemas/llm_schema.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    GLM = "glm"
    GROQ = "groq"


class LLMMode(str, Enum):
    """Simple preset modes for LLM selection"""
    LOCAL_ONLY = "local_only"      # Use only Ollama (local LLM)
    GLM_ONLY = "glm_only"          # Use only GLM API
    COMBINED = "combined"          # Combine both Ollama and GLM (ensemble)


class MultiLLMStrategy(str, Enum):
    SINGLE = "single"  # Use primary model only
    ENSEMBLE = "ensemble"  # Run multiple models and merge results
    CASCADE = "cascade"  # Try primary, fallback to secondary on failure


class ModelConfig(BaseModel):
    """Configuration for a single model"""
    provider: LLMProvider
    model: str
    weight: float = 1.0  # For ensemble weighted voting


class SimpleLLMConfig(BaseModel):
    """Simple LLM configuration with preset modes"""
    mode: LLMMode

    # Optional model overrides (if not specified, uses defaults)
    local_model: str = "llama3.1:8b"      # Default for Ollama
    glm_model: str = "glm-4.5-flash"         # Default for GLM

    # For combined mode
    local_weight: float = 0.6             # Weight for local model in combined mode
    glm_weight: float = 0.4               # Weight for GLM in combined mode


class LLMConfiguration(BaseModel):
    """
    Multi-LLM configuration supporting single, ensemble, and cascade modes.

    Simple mode (recommended for most users):
    {
        "mode": "local_only"    // Use only Ollama
        "mode": "glm_only"      // Use only GLM API
        "mode": "combined"      // Combine both (ensemble)
    }

    Advanced configuration:
    {
        "strategy": "single",
        "primary": {"provider": "ollama", "model": "llama3.1:8b"}
    }

    Examples:
    1. Simple - Local only:
       {"mode": "local_only"}

    2. Simple - GLM only:
       {"mode": "glm_only"}

    3. Simple - Combined:
       {"mode": "combined"}

    4. Advanced - Single model:
       {"strategy": "single", "primary": {"provider": "ollama", "model": "llama3.1:8b"}}

    5. Advanced - Ensemble:
       {
           "strategy": "ensemble",
           "primary": {"provider": "ollama", "model": "llama3.1:8b", "weight": 0.6},
           "secondary": [{"provider": "glm", "model": "glm-4.5-flash", "weight": 0.4}]
       }
    """
    # Simple mode (use this for easy configuration)
    mode: Optional[LLMMode] = None

    # Advanced configuration (optional, overrides mode if set)
    strategy: Optional[MultiLLMStrategy] = None
    primary: Optional[ModelConfig] = None
    secondary: List[ModelConfig] = []

    # Model overrides for simple mode
    local_model: str = "llama3.1:8b"
    glm_model: str = "glm-4.5-flash"  # Z.AI GLM-4.7 model

    # Ensemble options
    merge_method: Literal["weighted", "majority", "concat"] = "weighted"
    local_weight: float = 0.6  # Weight for local model in combined mode
    glm_weight: float = 0.4    # Weight for GLM in combined mode

    # Cascade options
    timeout_seconds: int = 120  # Timeout before falling back
    max_retries: int = 1

    # Per-type model override (optional)
    models_by_type: Optional[Dict[str, ModelConfig]] = Field(
        None,
        description="Override model for specific test types (e.g., {'functional': {...}, 'negative': {...}})"
    )


class LLMResult(BaseModel):
    """Result from LLM generation with metadata"""
    content: str
    model_used: str
    provider: LLMProvider
    generation_time_ms: int
    is_fallback: bool = False


class EnsembleResult(BaseModel):
    """Result from ensemble generation"""
    merged_content: str
    individual_results: List[LLMResult]
    merge_method: str
    agreement_score: float
