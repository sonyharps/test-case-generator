from datetime import datetime
import asyncio
from typing import Union, Optional

from app.pipeline.preprocessor.preprocessor import preprocess
from app.pipeline.llm.llm_router import get_llm_client
from app.pipeline.llm.multi_llm_router import get_llm_router, MultiLLMRouter
from app.schemas.llm_schema import LLMConfiguration
from app.core.config import settings

from app.pipeline.postprocessor.parser import (
    parse_any_json,
    parse_testcases_json,
)
from app.pipeline.postprocessor.validator import validate_testcases

from app.pipeline.analyzer.coverage import compute_coverage
from app.pipeline.analyzer.risk import evaluate_risk

from app.pipeline.prompt_builder.summary_prompt_v71 import build_summary_prompt
from app.pipeline.prompt_builder.test_space_prompt import build_test_space_prompt
from app.pipeline.prompt_builder.tc_prompt import build_functional_prompt
from app.pipeline.prompt_builder.negative_prompt import build_negative_prompt
from app.pipeline.prompt_builder.boundary_prompt import build_boundary_prompt
from app.pipeline.prompt_builder.tc_extractor_prompt import build_tc_extractor_prompt

from app.services.rag_service import rag_service


# =====================================================
# SUMMARY NORMALIZER (SINGLE SOURCE OF TRUTH)
# =====================================================
def normalize_summary(raw):
    if isinstance(raw, list):
        raw = raw[0] if raw else {}

    if not isinstance(raw, dict):
        raw = {}

    return {
        "id": raw.get("id", "REQ-001"),
        "nama": raw.get("nama") or raw.get("judul") or "",
        "deskripsi": raw.get("deskripsi") or raw.get("description") or "",
        "prioritas": raw.get("prioritas", ""),
        "kategori": raw.get("kategori", ""),
    }


# =====================================================
# ORCHESTRATOR
# =====================================================
async def orchestrate(
    requirement: str,
    model: Union[str, LLMConfiguration] = settings.DEFAULT_LLM_MODEL,
    generate_boundary: bool = True,
    include_risk: bool = True,
    rag_context: dict = None,
    llm_router: Optional[MultiLLMRouter] = None,
):
    """
    Orchestrate test case generation with support for multi-LLM configurations.

    Args:
        requirement: The requirement text
        model: Model name (str) or LLMConfiguration for multi-LLM strategies
        generate_boundary: Whether to generate boundary test cases
        include_risk: Whether to include risk assessment
        rag_context: Optional RAG context for augmented generation
        llm_router: Optional pre-configured MultiLLMRouter (takes precedence over model)

    Returns:
        Dictionary with generated test cases and metadata
    """
    # -------------------------------------------------
    # 1. PREPROCESS
    # -------------------------------------------------
    pre = preprocess(requirement)
    clean_req = pre.get("clean_requirement", "")
    domain = pre.get("domain", "")

    # Use provided router or create from model/config
    if llm_router is None:
        llm_router = get_llm_router(model)

    # -------------------------------------------------
    # 2. SUMMARY + 3. TEST SPACE (PARALLEL)
    # -------------------------------------------------
    # Run summary and space generation in parallel since they're independent
    summary_raw, space_raw = await asyncio.gather(
        llm_router.generate(build_summary_prompt(clean_req, domain)),
        llm_router.generate(build_test_space_prompt(pre))
    )

    summary_parsed = parse_any_json(summary_raw)
    summary = normalize_summary(summary_parsed)
    test_space = parse_any_json(space_raw)

    if not isinstance(test_space, dict):
        print("⚠️ TEST SPACE INVALID → FALLBACK")
        test_space = {
            "success": [{
                "scenario": "Happy path utama",
                "goal": "Fungsi utama berjalan normal"
            }],
            "failure": [{
                "scenario": "Input tidak valid",
                "goal": "Sistem menolak input"
            }],
            "boundary": [{
                "scenario": "Nilai batas",
                "goal": "Sistem menangani boundary"
            }],
        }

    success_space = test_space.get("success") or []
    failure_space = test_space.get("failure") or []
    boundary_space = test_space.get("boundary") or []

    print("=== TEST SPACE FINAL ===")
    print("SUCCESS:", success_space)
    print("FAILURE:", failure_space)
    print("BOUNDARY:", boundary_space)

    # -------------------------------------------------
    # 4-6. GENERATE TEST CASES (PARALLEL)
    # -------------------------------------------------
    # Define async functions for each test case type
    # Use llm_router for per-type model selection support
    async def generate_functional():
        if not success_space:
            return []

        base_prompt = build_functional_prompt(success_space)
        augmented_prompt = (
            rag_service.build_augmented_prompt(
                requirement=clean_req,
                context=rag_context,
                test_type="functional",
                base_prompt=base_prompt
            ) if rag_context else base_prompt
        )

        # Generate raw and JSON in sequence (they depend on each other)
        # Use llm_router with test_type for per-type model selection
        functional_raw = await llm_router.generate(augmented_prompt, test_type="functional")
        functional_json_raw = await llm_router.generate(build_tc_extractor_prompt(functional_raw), test_type="functional")
        functional_json = parse_any_json(functional_json_raw)

        if isinstance(functional_json, list):
            return parse_testcases_json(functional_json, prefix="TC-F")
        else:
            print("⚠️ FUNCTIONAL JSON INVALID")
            return []

    async def generate_negative():
        if not failure_space:
            return []

        base_prompt = build_negative_prompt(failure_space)
        augmented_prompt = (
            rag_service.build_augmented_prompt(
                requirement=clean_req,
                context=rag_context,
                test_type="negative",
                base_prompt=base_prompt
            ) if rag_context else base_prompt
        )

        # Generate raw and JSON in sequence
        negative_raw = await llm_router.generate(augmented_prompt, test_type="negative")
        negative_json_raw = await llm_router.generate(build_tc_extractor_prompt(negative_raw), test_type="negative")
        negative_json = parse_any_json(negative_json_raw)

        if isinstance(negative_json, list):
            return parse_testcases_json(negative_json, prefix="TC-N")
        return []

    async def generate_boundary():
        if not (generate_boundary and boundary_space):
            return []

        base_prompt = build_boundary_prompt(boundary_space)
        augmented_prompt = (
            rag_service.build_augmented_prompt(
                requirement=clean_req,
                context=rag_context,
                test_type="boundary",
                base_prompt=base_prompt
            ) if rag_context else base_prompt
        )

        # Generate raw and JSON in sequence
        boundary_raw = await llm_router.generate(augmented_prompt, test_type="boundary")
        boundary_json_raw = await llm_router.generate(build_tc_extractor_prompt(boundary_raw), test_type="boundary")
        boundary_json = parse_any_json(boundary_json_raw)

        if isinstance(boundary_json, list):
            return parse_testcases_json(boundary_json, prefix="TC-B")
        return []

    # Run all three test case types in parallel
    functional, negative, boundary = await asyncio.gather(
        generate_functional(),
        generate_negative(),
        generate_boundary()
    )

    # HARD FALLBACK — FUNCTIONAL MUST EXIST
    if not functional:
        functional = [{
            "tc_id": "TC-F-001",
            "title": "Fallback Functional Test Case",
            "preconditions": ["Requirement dapat diproses"],
            "steps": ["Sistem memproses alur utama"],
            "expected_result": ["Tidak terjadi error sistem"],
        }]

    print("=== FUNCTIONAL FINAL ===")
    print(functional)
    print("=== NEGATIVE FINAL ===")
    print(negative)
    print("=== BOUNDARY FINAL ===")
    print(boundary)
    # -------------------------------------------------
    # 7. VALIDATION (MUTATE IN-PLACE)
    # -------------------------------------------------
    functional = validate_testcases(functional) or []
    negative = validate_testcases(negative) or []
    boundary = validate_testcases(boundary) or []

    # -------------------------------------------------
    # 8. ANALYSIS
    # -------------------------------------------------
    coverage = {
        "functional": len(functional),
        "negative": len(negative),
        "boundary": len(boundary),
    }

    risk = (
        evaluate_risk(functional, negative, boundary)
        if include_risk
        else {"level": "N/A", "notes": []}
    )

    # -------------------------------------------------
    # 9. RETURN (CLEAN CONTRACT)
    # -------------------------------------------------
    return {
        "summary": summary,
        "functional": functional,
        "negative": negative,
        "boundary": boundary,
        "coverage": coverage,
        "risk": risk,
        "metadata": {
            "model": model,
            "domain": domain,
            "generated_at": datetime.utcnow().isoformat(),
        },
    }
