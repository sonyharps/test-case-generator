# app/services/orchestrator.py
import time
import json
from app.services.prompt_orchestrator import (
    functional_json_prompt, negative_json_prompt, boundary_json_prompt, summary_prompt
)
from app.services.langchain_helpers import OllamaLLMWrapper
from app.schemas.tc_schema import OrchestratorResult

def call_with_retries(llm_wrapper, prompt, tries=3):
    last_raw = None
    for i in range(tries):
        raw = llm_wrapper(prompt)
        last_raw = raw
        cleaned = raw.strip()
        # remove common code fences
        if "```" in cleaned:
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        # try direct parse
        try:
            parsed = json.loads(cleaned)
            return parsed
        except json.JSONDecodeError:
            # try slice between first [ and last ] (common LLM behaviour)
            try:
                start = cleaned.find('[')
                end = cleaned.rfind(']')
                if start != -1 and end != -1 and end > start:
                    fragment = cleaned[start:end+1]
                    parsed = json.loads(fragment)
                    return parsed
            except Exception:
                pass
            # otherwise continue retry
            continue
    raise ValueError(f"LLM failed to return valid JSON after {tries} tries. Last raw:\n{last_raw}")

def orchestrate(requirement: str,
                model="llama3.1:8b",
                generate_boundary=True,
                include_risk=True):
    llm = OllamaLLMWrapper(model=model)

    # 1) functional
    fn_prompt = functional_json_prompt(requirement)
    functional = call_with_retries(llm, fn_prompt, tries=3)

    # 2) negative
    neg_prompt = negative_json_prompt(requirement)
    negative = call_with_retries(llm, neg_prompt, tries=3)

    # 3) boundary (optional)
    boundary = []
    if generate_boundary:
        bnd_prompt = boundary_json_prompt(requirement)
        boundary = call_with_retries(llm, bnd_prompt, tries=3)

    # 4) summary & risk
    summ_prompt = summary_prompt(functional, negative, boundary)
    summary_raw = llm(summ_prompt).strip()

    # simple heuristic for risk level
    text_lower = summary_raw.lower()
    risk_level = "low"
    if any(w in text_lower for w in ["critical", "high", "severe", "major"]):
        risk_level = "high"
    elif any(w in text_lower for w in ["medium", "moderate", "possible", "warning"]):
        risk_level = "medium"

    risk = {"level": risk_level, "notes": [summary_raw[:400]]} if include_risk else {"level":"low","notes":[]}

    coverage_matrix = {
        "functional_count": len(functional),
        "negative_count": len(negative),
        "boundary_count": len(boundary)
    }

    result = {
        "functional": functional,
        "negative": negative,
        "boundary": boundary,
        "summary": summary_raw,
        "risk": risk,
        "coverage_matrix": coverage_matrix,
        "metadata": {"model": model, "time": time.strftime("%Y-%m-%dT%H:%M:%S")},
        "requirement": requirement,        # ← wajib
        "model_used": model,  
    }

    # lightweight validation with pydantic (do not crash; annotate validation error)
    try:
        OrchestratorResult.parse_obj({
            "functional": functional,
            "negative": negative,
            "boundary": boundary,
            "summary": summary_raw,
            "risk": risk,
            "coverage_matrix": coverage_matrix
        })
    except Exception as e:
        result["validation_error"] = str(e)

    return result
