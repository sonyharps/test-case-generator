from datetime import datetime
import json

# --- PREPROCESSOR ---
from app.pipeline.preprocessor.preprocessor import preprocess

# --- PROMPT BUILDERS ---
from app.pipeline.prompt_builder.summary_flexible_prompt import build_flexible_summary_prompt
from app.pipeline.prompt_builder.tc_prompt import build_functional_prompt
from app.pipeline.prompt_builder.negative_prompt import build_negative_prompt
from app.pipeline.prompt_builder.boundary_prompt import build_boundary_prompt
from app.pipeline.prompt_builder.batch_prompt import build_batched_prompt

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
            "time": datetime.utcnow().isoformat(),
            "batched": False
        }
    }


async def orchestrate_batched(
    requirement: str,
    model: str = "llama3.1:8b",
    generate_boundary: bool = True,
    include_risk: bool = True
):
    """
    ORCHESTRATOR ENGINE V7 - BATCHED MODE

    CRITICAL OPTIMIZATION: Reduces API calls from 4 to 1 by batching all test types
    into a single LLM request. This dramatically reduces rate limit issues.

    Capacity: 7-30 concurrent users (depending on usage pattern)
    Previous: 4 requests per generation
    Now: 1 request per generation
    """
    # -----------------------------
    # 1. PREPROCESS
    # -----------------------------
    pre = preprocess(requirement)

    # -----------------------------
    # 2. BUILD BATCHED PROMPT
    # -----------------------------
    batched_prompt = build_batched_prompt(pre, include_boundary=generate_boundary)

    # -----------------------------
    # 3. LLM
    # -----------------------------
    llm = get_llm_client(model)

    # -----------------------------
    # 4. SINGLE BATCHED REQUEST
    # -----------------------------
    print("\n===== BATCHED MODE - Single API Call =====")
    raw_response = await llm.generate(batched_prompt)
    print(f"Response length: {len(raw_response)} characters")
    print("==========================\n")

    # -----------------------------
    # 5. PARSE BATCHED RESPONSE
    # -----------------------------
    try:
        result = parse_any_json(raw_response)
    except Exception as e:
        # Fallback: try to extract JSON
        from app.pipeline.postprocessor.parser import extract_partial_json
        result = extract_partial_json(raw_response)

    # Extract sections
    summary = result.get("summary", {})
    functional_list = result.get("functional", [])
    negative_list = result.get("negative", [])
    boundary_list = result.get("boundary", [])

    # Parse test cases with proper prefixes
    functional = parse_testcases_json(
        json.dumps(functional_list),
        prefix="TC-F"
    ) if functional_list else []

    negative = parse_testcases_json(
        json.dumps(negative_list),
        prefix="TC-N"
    ) if negative_list else []

    boundary = parse_testcases_json(
        json.dumps(boundary_list),
        prefix="TC-B"
    ) if boundary_list else []

    # -----------------------------
    # 6. VALIDATION
    # -----------------------------
    if functional:
        validate_testcases(functional)
    if negative:
        validate_testcases(negative)
    if boundary:
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
            "time": datetime.utcnow().isoformat(),
            "batched": True,
            "api_calls": 1  # Critical: only 1 API call instead of 4
        }
    }
