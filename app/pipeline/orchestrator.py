# app/pipeline/orchestrator.py

from datetime import datetime

# --- PREPROCESSOR ---
from app.pipeline.preprocessor.preprocessor import preprocess

# --- PROMPT BUILDERS ---
from app.pipeline.prompt_builder.summary_prompt import build_summary_prompt
from app.pipeline.prompt_builder.tc_prompt import build_functional_prompt
from app.pipeline.prompt_builder.negative_prompt import build_negative_prompt
from app.pipeline.prompt_builder.boundary_prompt import build_boundary_prompt

# --- LLM RUNTIME ---
from app.pipeline.llm.llm_router import get_llm_client

# --- POSTPROCESSOR ---
from app.pipeline.postprocessor.parser import parse_testcases_json
from app.pipeline.postprocessor.validator import validate_testcases

# --- ANALYZER ---
from app.pipeline.analyzer.coverage import compute_coverage
from app.pipeline.analyzer.risk import evaluate_risk


# ============================================================
# Utility: ensure always list (fix raw LLM output)
# ============================================================
def ensure_list(data):
    if data is None:
        return []
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []


# ============================================================
# ORCHESTRATOR MAIN
# ============================================================
async def orchestrate(
    requirement: str,
    model: str = "llama3.1:8b",
    generate_boundary: bool = True,
    include_risk: bool = True
):
    """
    Enterprise Orchestrator V5
    - Preprocess
    - Build prompts
    - Query LLM
    - Parse JSON
    - Validate
    - Analyze
    - Return structured output safe for UI
    """

    # -----------------------------
    # 1. PREPROCESS
    # -----------------------------
    pre = preprocess(requirement)

    # -----------------------------
    # 2. PROMPTS
    # -----------------------------
    prompts = {
        "summary": build_summary_prompt(pre),
        "functional": build_functional_prompt(pre),
        "negative": build_negative_prompt(pre),
    }

    if generate_boundary:
        prompts["boundary"] = build_boundary_prompt(pre)

    # -----------------------------
    # 3. LLM
    # -----------------------------
    llm = get_llm_client(model)

    # -----------------------------
    # 4. EXECUTE LLM CALLS
    # -----------------------------
    summary_raw = await llm.generate(prompts["summary"])
    from app.pipeline.postprocessor.parser import parse_any_json
    summary = parse_any_json(summary_raw) or {}
    functional_raw = await llm.generate(prompts["functional"])
    negative_raw = await llm.generate(prompts["negative"])
    boundary_raw = "[]" if not generate_boundary else await llm.generate(prompts["boundary"])

    # Debug (aktifkan jika perlu)
    print("\n===== RAW LLM OUTPUT =====")
    print("SUMMARY:", summary_raw[:300], "...")
    print("FUNCTIONAL:", functional_raw[:300], "...")
    print("NEGATIVE:", negative_raw[:300], "...")
    print("BOUNDARY:", boundary_raw[:300], "...")
    print("==========================\n")

    # -----------------------------
    # 5. PARSE JSON
    # -----------------------------
    #summary = parse_any_json(summary_raw)
    #functional = parse_any_json(functional_raw)
    #negative = parse_any_json(negative_raw)
    #boundary = parse_any_json(boundary_raw)

    functional = parse_testcases_json(functional_raw, prefix="TC-F")
    negative = parse_testcases_json(negative_raw, prefix="TC-N")
    boundary = parse_testcases_json(boundary_raw, prefix="TC-B")



    # -----------------------------
    # 6. VALIDATION
    # -----------------------------
    validate_testcases(functional)
    validate_testcases(negative)
    validate_testcases(boundary)

    # -----------------------------
    # 7. ANALYZER
    # -----------------------------
    coverage = compute_coverage(
        functional=functional,
        negative=negative,
        boundary=boundary
    )

    risk = evaluate_risk(
        functional=functional,
        negative=negative,
        boundary=boundary
    ) if include_risk else {"level": "N/A", "notes": []}

    # -----------------------------
    # 8. FINAL RESPONSE
    # -----------------------------
    return {
        "summary": summary,
        "functional": functional,
        "negative": negative,
        "boundary": boundary,
        "coverage_matrix": coverage,
        "risk": risk,
        "metadata": {
            "model": model,
            "domain": pre.get("domain", "unknown"),
            "time": datetime.utcnow().isoformat()
        }
    }
