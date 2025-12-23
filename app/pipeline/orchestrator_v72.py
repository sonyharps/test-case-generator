from datetime import datetime

from app.pipeline.preprocessor.preprocessor import preprocess
from app.pipeline.llm.llm_router import get_llm_client

from app.pipeline.postprocessor.parser import parse_any_json, parse_testcases_json
from app.pipeline.postprocessor.validator import validate_testcases
from app.pipeline.analyzer.coverage import compute_coverage
from app.pipeline.analyzer.risk import evaluate_risk

# PROMPTS
from app.pipeline.prompt_builder.summary_prompt_v71 import build_summary_prompt
from app.pipeline.prompt_builder.tc_plan_prompt_v71 import build_testcase_plan_prompt
from app.pipeline.prompt_builder.tc_space_prompt_v72 import build_test_space_prompt
from app.pipeline.prompt_builder.tc_generator_prompt_v71 import build_tc_generator_prompt


async def orchestrate(
    requirement,
    model="llama3.1:8b",
    generate_boundary=True,
    include_risk=True
):
    # ---------------------------
    # 1. PREPROCESS
    # ---------------------------
    pre = preprocess(requirement)
    clean_req = pre["clean_requirement"]
    domain = pre["domain"]

    # ---------------------------
    # 2. LLM CLIENT
    # ---------------------------
    llm = get_llm_client(model)

    # ---------------------------
    # STAGE 1 — SUMMARY
    # ---------------------------
    summary_raw = await llm.generate(
        build_summary_prompt(clean_req, domain)
    )
    summary = parse_any_json(summary_raw)

    # ---------------------------
    # STAGE 2 — TEST PLAN
    # ---------------------------
    plan_raw = await llm.generate(
        build_testcase_plan_prompt(clean_req, domain)
    )
    expanded_plan = parse_any_json(plan_raw)

    # ---------------------------
    # STAGE 2.5 — TEST SPACE ANALYSIS 🔥
    # ---------------------------
    space_raw = await llm.generate(
        build_test_space_prompt(clean_req, domain)
    )
    test_space = parse_any_json(space_raw)

    functional_space = test_space.get("functional_space", [])
    negative_space = test_space.get("negative_space", [])
    boundary_space = test_space.get("boundary_space", [])

    # ---------------------------
    # STAGE 3 — TEST CASE GENERATION
    # ---------------------------
    functional = []
    negative = []
    boundary = []

    # Functional
    for intent in functional_space:
        raw = await llm.generate(
            build_tc_generator_prompt(
                expanded_plan=expanded_plan,
                req=clean_req,
                domain=domain,
                tc_type="functional",
                focus=intent
            )
        )
        functional.extend(parse_testcases_json(raw, prefix="TC-F"))

    # Negative
    for intent in negative_space:
        raw = await llm.generate(
            build_tc_generator_prompt(
                expanded_plan=expanded_plan,
                req=clean_req,
                domain=domain,
                tc_type="negative",
                focus=intent
            )
        )
        negative.extend(parse_testcases_json(raw, prefix="TC-N"))

    # Boundary
    if generate_boundary:
        for intent in boundary_space:
            raw = await llm.generate(
                build_tc_generator_prompt(
                    expanded_plan=expanded_plan,
                    req=clean_req,
                    domain=domain,
                    tc_type="boundary",
                    focus=intent
                )
            )
            boundary.extend(parse_testcases_json(raw, prefix="TC-B"))

    # ---------------------------
    # 4. VALIDATION
    # ---------------------------
    validate_testcases(functional)
    validate_testcases(negative)
    validate_testcases(boundary)

    # ---------------------------
    # 5. ANALYZER
    # ---------------------------
    coverage = compute_coverage(functional, negative, boundary)
    risk = (
        evaluate_risk(functional, negative, boundary)
        if include_risk
        else {"level": "N/A", "notes": []}
    )

    # ---------------------------
    # 6. RESPONSE
    # ---------------------------
    return {
        "summary": summary,
        "functional": functional,
        "negative": negative,
        "boundary": boundary,
        "coverage_matrix": coverage,
        "risk": risk,
        "metadata": {
            "model": model,
            "domain": domain,
            "time": datetime.utcnow().isoformat()
        }
    }
