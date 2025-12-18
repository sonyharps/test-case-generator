from datetime import datetime

# --- PREPROCESSOR ---
from app.pipeline.preprocessor.preprocessor import preprocess

# --- PROMPT BUILDERS ---
from app.pipeline.prompt_builder.summary_flexible_prompt import build_flexible_summary_prompt
from app.pipeline.prompt_builder.tc_prompt import build_functional_prompt
from app.pipeline.prompt_builder.negative_prompt import build_negative_prompt
from app.pipeline.prompt_builder.boundary_prompt import build_boundary_prompt

# --- LLM ROUTER ---
from app.pipeline.llm.llm_router import get_llm_client

# --- PARSER ---
from app.pipeline.postprocessor.parser import (
    parse_any_json,
    parse_testcases_json,
)

# --- VALIDATION ---
from app.pipeline.postprocessor.validator import validate_testcases

# --- ANALYZER ---
from app.pipeline.analyzer.coverage import compute_coverage
from app.pipeline.analyzer.risk import evaluate_risk





async def orchestrate(
    requirement: str,
    model: str = "llama3.1:8b",
    generate_boundary: bool = True,
    include_risk: bool = True
):
    """
    ORCHESTRATOR ENGINE V6
    Clean summary + stable TC generation + anti-noise parser.
    """

    # -----------------------------
    # 1. PREPROCESS
    # -----------------------------
    pre = preprocess(requirement)

    # -----------------------------
    # 2. PROMPTS
    # -----------------------------
    prompts = {
        "summary": build_flexible_summary_prompt(pre),
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
    # 4. GENERATE RAW OUTPUTS
    # -----------------------------
    summary_raw = await llm.generate(prompts["summary"])
    functional_raw = await llm.generate(prompts["functional"])
    negative_raw = await llm.generate(prompts["negative"])
    boundary_raw = (
        await llm.generate(prompts["boundary"])
        if generate_boundary else
        "[]"
    )

   

    print("\n===== RAW LLM OUTPUT =====")
    print("SUMMARY:", summary_raw[:300], "...")
    print("FUNCTIONAL:", functional_raw[:300], "...")
    print("NEGATIVE:", negative_raw[:300], "...")
    print("BOUNDARY:", boundary_raw[:300], "...")
    print("==========================\n")

     # --- FIX PARTIAL JSON ---
    from app.pipeline.postprocessor.parser import extract_partial_json

    summary = extract_partial_json(summary_raw)

    # -----------------------------
    # 5. PARSE RESULTS
    # -----------------------------
    summary = parse_any_json(summary_raw)
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
