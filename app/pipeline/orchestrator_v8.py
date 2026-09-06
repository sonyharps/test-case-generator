"""
Orchestrator V8 — Document-driven powerful test case generation.

Architecture shift from V7:
- V7 (weak-model pattern): 6-8 small LLM calls, two-pass JSON (generate + extractor),
  RAG chunk snippets (~200 chars), low temperature (0.2).
- V8 (powerful-model pattern): 3-4 LLM calls, single-pass structured JSON, FULL document
  text fed to the model, higher temperature (0.4) for diversity.

Flow:
  [LLM #1 ANALYZE] read full document → summary + rich test space (1 call)
  [LLM #2-4 GENERATE] one call per type (functional/negative/boundary), run in parallel
  [CODE] parse + validate + risk + coverage → return SAME shape as v7 (backward compatible)

The V8 entry point is `orchestrate_v8()`. It is invoked by the orchestrator API router
when a `document_id` is supplied; otherwise V7 runs as before.
"""

from datetime import datetime
import asyncio
import inspect
from typing import Union, Optional, List, Dict, Any

from app.pipeline.preprocessor.preprocessor import preprocess
from app.pipeline.llm.multi_llm_router import get_llm_router, MultiLLMRouter
from app.schemas.llm_schema import LLMConfiguration
from app.core.config import settings

from app.pipeline.postprocessor.parser import parse_any_json, parse_testcases_json, salvage_tc_array
from app.pipeline.postprocessor.validator import validate_testcases

from app.pipeline.analyzer.coverage import compute_coverage
from app.pipeline.analyzer.risk import evaluate_risk

from app.pipeline.prompt_builder.v8_analyze_prompt import build_v8_analyze_prompt
from app.pipeline.prompt_builder.v8_generate_prompt import build_v8_generate_prompt
from app.pipeline.prompt_builder.v8_full_generate_prompt import build_v8_full_generate_prompt
from app.pipeline.prompt_builder.v8_category_prompt import build_v8_category_prompt
from app.pipeline.prompt_builder.v8_summary_prompt import build_v8_summary_prompt
from app.services.pii_redactor import redact as redact_pii

# Generation params for V8 — favor diversity and high output volume.
# 65536: "max" volume preset (70/70/60 targets) with ISO/IEC/IEEE 29119-3 fields needs
# >49k completion tokens per category at times; API accepts up to 98k
# (tested). 65536 covers ~100 TC/category with salvage as safety net.
V8_MAX_TOKENS_ANALYZE = 8192
V8_MAX_TOKENS_GENERATE = 65536
V8_TEMPERATURE_ANALYZE = 0.4
V8_TEMPERATURE_GENERATE = 0.5

# Max document chars fed to the model (keeps prompt within context window safely).
MAX_DOC_CHARS_ANALYZE = 60000
MAX_DOC_CHARS_GENERATE = 20000


# =====================================================
# SUMMARY NORMALIZER (mirrors v7 — single source of truth for the summary shape)
# =====================================================
def normalize_summary(raw) -> Dict[str, Any]:
    """Normalize the LLM summary into the shape the frontend expects.

    Preserves the Indonesian keys (nama/deskripsi/prioritas/kategori/fitur_kunci)
    consumed by the SummaryCard UI component.
    """
    if isinstance(raw, list):
        raw = raw[0] if raw else {}

    if not isinstance(raw, dict):
        raw = {}

    fitur = raw.get("fitur_kunci") or raw.get("fiturKunci") or []

    return {
        "id": raw.get("id", "REQ-001"),
        "nama": raw.get("nama") or raw.get("judul") or "",
        "deskripsi": raw.get("deskripsi") or raw.get("description") or "",
        "prioritas": raw.get("prioritas", ""),
        "kategori": raw.get("kategori", ""),
        "fitur_kunci": fitur if isinstance(fitur, list) else [],
    }


def _doc_preview(text: str, limit: int) -> str:
    if not text:
        return ""
    return text[:limit]


async def _generate_with_params(
    router: MultiLLMRouter,
    prompt: str,
    test_type: str,
    max_tokens: int,
    temperature: float,
) -> str:
    """Call router.generate, forwarding generation params if the router supports them.

    Inspects the signature so older MultiLLMRouter versions (without the kwargs)
    still work by falling back to a plain call.
    """
    sig = inspect.signature(router.generate)
    kwargs: Dict[str, Any] = {}
    if "max_tokens" in sig.parameters:
        kwargs["max_tokens"] = max_tokens
    if "temperature" in sig.parameters:
        kwargs["temperature"] = temperature
    return await router.generate(prompt, test_type=test_type, **kwargs)


# =====================================================
# ORCHESTRATOR V8
# =====================================================
async def orchestrate_v8(
    document_text: str,
    model: Union[str, LLMConfiguration] = settings.DEFAULT_LLM_MODEL,
    requirement: Optional[str] = None,
    generate_boundary: bool = True,
    include_risk: bool = True,
    target_per_scenario: int = 2,
    llm_router: Optional[MultiLLMRouter] = None,
    targets: Optional[Dict[str, int]] = None,
    use_history: bool = True,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Orchestrate powerful, document-driven test case generation.

    Args:
        document_text: FULL source document text (PRD/user story/etc.).
        model: Model name (str) or LLMConfiguration for multi-LLM strategies.
        requirement: Optional focus requirement (free-text supplement to the document).
        generate_boundary: Whether to generate boundary test cases.
        include_risk: Whether to include risk assessment.
        target_per_scenario: Number of test cases to demand per scenario (drives volume).
        llm_router: Optional pre-configured MultiLLMRouter (takes precedence over model).
        targets: Explicit per-category minimums {functional, negative, boundary}.
                Overrides the target_per_scenario formula (used by the volume knob).
        use_history: RAG exemplar learning — retrieve similar historical TCs
                (same user) and inject them as style/depth reference examples.
        user_id: Owner id used to scope the historical retrieval.

    Returns:
        Dictionary with the SAME shape as v7's orchestrate() so the frontend stays
        compatible: summary, functional[], negative[], boundary[], coverage, risk, metadata.
    """
    # -------------------------------------------------
    # 1. PREPROCESS (light — used only for domain tagging)
    # -------------------------------------------------
    pre = preprocess(requirement or document_text[:2000])
    domain = pre.get("domain", "")

    if llm_router is None:
        llm_router = get_llm_router(model)

    # -------------------------------------------------
    # 2. GENERATION (parallel category calls — high volume)
    # -------------------------------------------------
    # Guardrail: scrub PII (account numbers, NIK, phone, email, card, tokens)
    # from the document BEFORE it leaves the machine for the cloud LLM. This
    # materially reduces sensitive-data exposure without changing semantics.
    safe_doc, pii_stats = redact_pii(document_text, return_stats=True)
    if pii_stats and sum(pii_stats.values()):
        print(f"🔒 PII redacted: {pii_stats}")

    # -------------------------------------------------
    # 2a. RAG EXEMPLAR LEARNING (optional)
    # Retrieve similar historical TCs → style/depth reference for the prompts.
    # Runs BEFORE the parallel calls; failures degrade silently to no-history.
    # -------------------------------------------------
    exemplars: List[str] = []
    if use_history:
        try:
            from app.services.exemplar_service import exemplar_service
            query = f"{(requirement or '')[:500]}\n{safe_doc[:2500]}"
            exemplars = await exemplar_service.retrieve_exemplars(
                query_text=query, user_id=user_id, k=6
            )
            print(f"📚 Exemplar learning: {len(exemplars)} referensi riwayat")
        except Exception as e:
            print(f"⚠️ Exemplar retrieval failed (continuing without): {e}")

    # V8.1 PARALLEL: one dedicated call per category, run concurrently.
    # Each call gets the FULL token budget for its category, so volume is
    # ~3x the old single-call design at roughly the same wall-clock time.
    # Explicit `targets` (volume knob) takes precedence over the formula.
    if targets:
        cat_targets = {
            "functional": int(targets.get("functional", 28)),
            "negative": int(targets.get("negative", 28)),
            "boundary": int(targets.get("boundary", 24)) if generate_boundary else 0,
        }
    else:
        cat_targets = {
            "functional": max(28, target_per_scenario * 14),
            "negative": max(28, target_per_scenario * 14),
            "boundary": max(24, target_per_scenario * 12) if generate_boundary else 0,
        }

    async def _run_category(cat: str, target: int) -> str:
        p = build_v8_category_prompt(
            cat, safe_doc, requirement=requirement, target=target, exemplars=exemplars
        )
        try:
            return await _generate_with_params(
                llm_router, p, test_type=cat,
                max_tokens=V8_MAX_TOKENS_GENERATE, temperature=V8_TEMPERATURE_GENERATE,
            )
        except Exception as first_err:
            # One retry — transient timeouts/errors shouldn't zero a category.
            # Rate limits (429) need a PAUSE before retrying: an instant re-fire
            # just bounces off the same window (OpenRouter upstream pools clear
            # within seconds).
            msg = str(first_err)
            if "429" in msg or "rate limit" in msg.lower():
                print(f"⚠️ V8 PARALLEL [{cat}] rate-limited → retry in 10s")
                await asyncio.sleep(10)
            else:
                print(f"⚠️ V8 PARALLEL [{cat}] error ({first_err}) → retrying once")
            return await _generate_with_params(
                llm_router, p, test_type=cat,
                max_tokens=V8_MAX_TOKENS_GENERATE, temperature=V8_TEMPERATURE_GENERATE,
            )

    async def _run_summary() -> Optional[Dict[str, Any]]:
        """Light 4th call: requirement summary + risk assessment (~500 tokens).
        Runs concurrently with the category calls — adds no wall-clock time."""
        p = build_v8_summary_prompt(safe_doc, requirement=requirement)
        try:
            raw = await _generate_with_params(
                llm_router, p, test_type="summary",
                max_tokens=V8_MAX_TOKENS_ANALYZE, temperature=V8_TEMPERATURE_ANALYZE,
            )
            parsed = parse_any_json(raw)
            return parsed if isinstance(parsed, dict) else None
        except Exception as e:
            print(f"⚠️ V8 PARALLEL [summary] FAILED: {e} → heuristic fallback")
            return None

    gen_tasks = [ _run_category(c, t) for c, t in cat_targets.items() if t > 0 ]
    summary_task = _run_summary()
    cat_results = await asyncio.gather(*gen_tasks, summary_task, return_exceptions=True)

    summary_result = cat_results[-1]
    cat_results = cat_results[:-1]

    # If EVERY category call failed (typically an upstream rate limit), saving
    # a near-empty "success" session is misleading — surface a clear error so
    # the user retries or switches model instead.
    _cat_errs = [r for r in cat_results if isinstance(r, Exception)]
    if _cat_errs and len(_cat_errs) == len(cat_results):
        raise RuntimeError(
            "Semua kategori gagal digenerate oleh model — kemungkinan rate limit "
            "OpenRouter (429). Coba lagi beberapa saat, atau ganti model di "
            "Pengaturan lanjutan. Detail: " + str(_cat_errs[0])[:200]
        )

    full_json: Dict[str, Any] = {}
    for (cat, target), res in zip(
        [(c, t) for c, t in cat_targets.items() if t > 0], cat_results
    ):
        if isinstance(res, Exception):
            print(f"⚠️ V8 PARALLEL [{cat}] FAILED: {res} → skipped")
            continue
        arr = parse_any_json(res)
        if isinstance(arr, dict):
            arr = arr.get(cat, [])
        if not isinstance(arr, list):
            # JSON was truncated mid-array (finish_reason=length) — salvage
            # the complete test-case objects instead of dropping everything.
            salvaged = salvage_tc_array(res)
            print(f"⚠️ V8 PARALLEL [{cat}] JSON truncated → salvaged {len(salvaged)} TC")
            arr = salvaged
        full_json[cat] = arr

    # Summary/risk: prefer the model's own document-grounded analysis; fall
    # back to a light heuristic only when the summary call failed.
    if isinstance(summary_result, dict) and summary_result.get("summary"):
        full_json["summary"] = summary_result.get("summary") or {}
        if isinstance(summary_result.get("risk"), dict):
            full_json["risk"] = summary_result["risk"]
        print("✅ V8 summary+risk from model")
    if not full_json.get("summary"):
        full_json["summary"] = {
            "id": "REQ-001",
            "nama": (requirement or "Generated Test Suite")[:120],
            "deskripsi": f"Auto-generated suite dari dokumen ({len(safe_doc):,} chars).",
            "prioritas": "High",
            "kategori": domain or "General",
            "fitur_kunci": [],
        }

    summary = normalize_summary(full_json.get("summary") or {})

    # Parse each category; parse_testcases_json enforces the list shape + tc_id.
    functional = parse_testcases_json(
        full_json.get("functional") if isinstance(full_json.get("functional"), list) else [],
        prefix="TC-F",
    )
    negative = parse_testcases_json(
        full_json.get("negative") if isinstance(full_json.get("negative"), list) else [],
        prefix="TC-N",
    )
    boundary = parse_testcases_json(
        full_json.get("boundary") if isinstance(full_json.get("boundary"), list) else [],
        prefix="TC-B",
    ) if generate_boundary else []

    # Prefer the model-supplied risk object when present, else compute later.
    model_risk = full_json.get("risk") if isinstance(full_json.get("risk"), dict) else None

    # HARD FALLBACK — functional must exist (mirrors v7 contract)
    if not functional:
        functional = [{
            "tc_id": "TC-F-001",
            "title": "Fallback Functional Test Case",
            "preconditions": ["Requirement dapat diproses"],
            "steps": ["Sistem memproses alur utama"],
            "expected_result": ["Tidak terjadi error sistem"],
        }]

    print(f"=== V8 SINGLE-CALL FINAL (functional={len(functional)}, "
          f"negative={len(negative)}, boundary={len(boundary)}) ===")

    # -------------------------------------------------
    # 4. VALIDATION (mutate in-place, mirrors v7)
    # -------------------------------------------------
    functional = validate_testcases(functional) or []
    negative = validate_testcases(negative) or []
    boundary = validate_testcases(boundary) or []

    # -------------------------------------------------
    # 5. ANALYSIS
    # -------------------------------------------------
    coverage = compute_coverage(functional, negative, boundary)

    # Prefer the model's risk assessment (it read the document); fall back to
    # the heuristic evaluator when missing/disabled.
    if include_risk and model_risk and model_risk.get("level"):
        risk = {
            "level": model_risk.get("level", "Medium"),
            "notes": model_risk.get("notes") if isinstance(model_risk.get("notes"), list) else [],
        }
    elif include_risk:
        risk = evaluate_risk(functional, negative, boundary)
    else:
        risk = {"level": "N/A", "notes": []}

    # -------------------------------------------------
    # 6. RETURN (same shape as v7 — backward compatible)
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
            "pipeline": "v8-parallel",
            "source_document_chars": len(document_text) if document_text else 0,
            "generated_at": datetime.utcnow().isoformat(),
        },
    }
