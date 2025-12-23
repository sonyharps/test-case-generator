from datetime import datetime

from app.pipeline.preprocessor.preprocessor import preprocess
from app.pipeline.llm.llm_router import get_llm_client
from app.pipeline.postprocessor.parser import parse_any_json, parse_testcases_json
from app.pipeline.postprocessor.validator import validate_testcases
from app.pipeline.analyzer.coverage import compute_coverage
from app.pipeline.analyzer.risk import evaluate_risk

from app.pipeline.prompt_builder.summary_prompt_v71 import build_summary_prompt
from app.pipeline.prompt_builder.test_space_prompt import build_test_space_prompt
from app.pipeline.prompt_builder.tc_prompt import build_functional_prompt
from app.pipeline.prompt_builder.negative_prompt import build_negative_prompt
from app.pipeline.prompt_builder.boundary_prompt import build_boundary_prompt
from app.pipeline.prompt_builder.tc_extractor_prompt import build_tc_extractor_prompt


def normalize_summary(summary_raw):
    if isinstance(summary_raw, list):
        summary_raw = summary_raw[0] if summary_raw else {}

    if not isinstance(summary_raw, dict):
        summary_raw = {}

    return {
        "id": summary_raw.get("id", "REQ-001"),
        "name": summary_raw.get("name", ""),
        "nama": summary_raw.get("name", ""),
        "description": summary_raw.get("deskripsi", ""),
        "deskripsi": summary_raw.get("deskripsi", ""),
        "priority": summary_raw.get("prioritas", ""),
        "prioritas": summary_raw.get("prioritas", ""),
        "category": summary_raw.get("kategori", ""),
        "kategori": summary_raw.get("kategori", ""),
    }


async def orchestrate(
    requirement,
    model="llama3.1:8b",
    generate_boundary=True,
    include_risk=True
):
    pre = preprocess(requirement)
    clean_req = pre["clean_requirement"]
    domain = pre["domain"]

    llm = get_llm_client(model)

    # SUMMARY
    summary_raw = await llm.generate(
        build_summary_prompt(clean_req, domain)
    )
    summary_parsed = parse_any_json(summary_raw)
    summary = normalize_summary(summary_parsed)

    # TEST SPACE
    space_raw = await llm.generate(
        build_test_space_prompt(pre)
    )
    test_space = parse_any_json(space_raw)

    if isinstance(test_space, list):
        test_space = {
            "success": test_space,
            "failure": [],
            "boundary": []
        }

    success_space = test_space.get("success", [])
    failure_space = test_space.get("failure", [])
    boundary_space = test_space.get("boundary", [])

    # FUNCTIONAL
    functional_raw = await llm.generate(
        build_functional_prompt(success_space)
    )
    functional_json_raw = await llm.generate(
        build_tc_extractor_prompt(functional_raw)
    )
    functional = parse_testcases_json(functional_json_raw, prefix="TC-F")

    # NEGATIVE
    negative_raw = await llm.generate(
        build_negative_prompt(failure_space)
    )
    negative_json_raw = await llm.generate(
        build_tc_extractor_prompt(negative_raw)
    )
    negative = parse_testcases_json(negative_json_raw, prefix="TC-N")

    # BOUNDARY
    boundary = []
    if generate_boundary and boundary_space:
        boundary_raw = await llm.generate(
            build_boundary_prompt(boundary_space)
        )
        boundary_json_raw = await llm.generate(
            build_tc_extractor_prompt(boundary_raw)
        )
        boundary = parse_testcases_json(boundary_json_raw, prefix="TC-B")

    validate_testcases(functional)
    validate_testcases(negative)
    validate_testcases(boundary)

    coverage = compute_coverage(functional, negative, boundary)
    risk = (
        evaluate_risk(functional, negative, boundary)
        if include_risk else {"level": "N/A", "notes": []}
    )

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
