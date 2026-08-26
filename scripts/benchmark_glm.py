#!/usr/bin/env python
"""Benchmark GLM test-case generation — measure TIME + TOKENS + VOLUME.

Runs the V8 single-call pipeline directly against the GLM coding-plan
endpoint with an aggressive (high) test-case target so we can measure:
  - wall-clock time
  - prompt_tokens / completion_tokens / total_tokens (from API usage)
  - number of test cases actually returned (functional/negative/boundary)

Usage:
    python scripts/benchmark_glm.py [document_id] [--model glm-5-turbo]
                                    [--target N] [--max-tokens N]
                                    [--runs 1]

Defaults: document_id=13 (PRD Dashboard AO), model=glm-5-turbo,
target_functional=60, target_negative=60, target_boundary=50,
max_tokens=24576, runs=1.
"""
import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
from sqlalchemy import select  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.document import UploadedDocument  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.pipeline.prompt_builder.v8_full_generate_prompt import (  # noqa: E402
    build_v8_full_generate_prompt,
)
from app.pipeline.prompt_builder.v8_category_prompt import (  # noqa: E402
    build_v8_category_prompt,
)
from app.pipeline.exporter.excel_exporter import excel_exporter  # noqa: E402

ENDPOINT = "https://api.z.ai/api/coding/paas/v4/chat/completions"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

DEFAULT_MODEL_BY_PROVIDER = {
    "glm": "glm-5-turbo",
    "groq": "openai/gpt-oss-120b",
    "gemini": "gemini-3.6-flash",
    "openrouter": "deepseek/deepseek-chat",
}


async def load_document_text(doc_id: int) -> tuple[str, str]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(UploadedDocument).where(UploadedDocument.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise SystemExit(f"Document id={doc_id} not found")
        return doc.title, doc.full_text or ""


async def call_glm_raw(
    prompt: str,
    model: str,
    max_tokens: int,
    temperature: float,
    api_key: str,
    retries: int = 3,
) -> tuple[str, dict]:
    """Call GLM API and return (content, usage_dict). Retries on 5xx."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "thinking": {"type": "disabled"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    timeout = httpx.Timeout(600.0, connect=60.0)
    last_err = None
    for attempt in range(1, retries + 1):
        async with httpx.AsyncClient(timeout=timeout, verify=True) as client:
            try:
                res = await client.post(ENDPOINT, json=payload, headers=headers)
                if res.status_code >= 500:
                    print(f"  API {res.status_code} (attempt {attempt}/{retries}), retrying in 10s...")
                    last_err = f"{res.status_code}: {res.text[:200]}"
                    await asyncio.sleep(10)
                    continue
                if res.status_code >= 400:
                    print(f"  API ERROR {res.status_code}: {res.text[:500]}")
                    res.raise_for_status()
                data = res.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content") or ""
                if not content.strip():
                    content = msg.get("reasoning_content") or ""
                usage = data.get("usage", {})
                finish_reason = data["choices"][0].get("finish_reason", "unknown")
                return content, {"usage": usage, "finish_reason": finish_reason}
            except httpx.HTTPStatusError:
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                print(f"  Network error (attempt {attempt}/{retries}): {type(e).__name__}, retrying...")
                last_err = str(e)
                await asyncio.sleep(10)
    raise RuntimeError(f"GLM API failed after {retries} retries. Last: {last_err}")


async def call_groq_raw(
    prompt: str,
    model: str,
    max_tokens: int,
    temperature: float,
    api_key: str,
    retries: int = 3,
) -> tuple[str, dict]:
    """Call Groq (OpenAI-compatible) and return (content, usage/finish meta)."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        # Groq caps llama-3.3-70b at 32768 completion tokens
        "max_tokens": min(max_tokens, 32768),
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    timeout = httpx.Timeout(300.0, connect=30.0)
    last_err = None
    for attempt in range(1, retries + 1):
        async with httpx.AsyncClient(timeout=timeout, verify=True) as client:
            try:
                res = await client.post(GROQ_ENDPOINT, json=payload, headers=headers)
                if res.status_code in (429, 500, 502, 503):
                    print(f"  Groq {res.status_code} (attempt {attempt}/{retries}), retry in 5s...")
                    last_err = f"{res.status_code}: {res.text[:200]}"
                    await asyncio.sleep(5)
                    continue
                if res.status_code >= 400:
                    print(f"  Groq ERROR {res.status_code}: {res.text[:300]}")
                    res.raise_for_status()
                data = res.json()
                content = data["choices"][0]["message"].get("content") or ""
                usage = data.get("usage", {})
                finish = data["choices"][0].get("finish_reason", "unknown")
                return content, {"usage": usage, "finish_reason": finish}
            except httpx.HTTPStatusError:
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                print(f"  Groq network error (attempt {attempt}/{retries}): {type(e).__name__}")
                last_err = str(e)
                await asyncio.sleep(5)
    raise RuntimeError(f"Groq API failed after {retries} retries. Last: {last_err}")


async def call_gemini_raw(
    prompt: str,
    model: str,
    max_tokens: int,
    temperature: float,
    api_key: str,
    retries: int = 3,
) -> tuple[str, dict]:
    """Call Gemini generateContent and return (content, usage/finish meta)."""
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    # gemini-2.0-* caps output at 8192; 2.5+ supports 65536
    gemini_out_cap = 8192 if "2.0" in model else 65536
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": min(max_tokens, gemini_out_cap),
        },
    }
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key,
    }
    timeout = httpx.Timeout(300.0, connect=30.0)
    last_err = None
    for attempt in range(1, retries + 1):
        async with httpx.AsyncClient(timeout=timeout, verify=True) as client:
            try:
                res = await client.post(endpoint, json=payload, headers=headers)
                if res.status_code in (429, 500, 503):
                    print(f"  Gemini {res.status_code} (attempt {attempt}/{retries}), retry in 10s...")
                    last_err = f"{res.status_code}: {res.text[:200]}"
                    await asyncio.sleep(10)
                    continue
                if res.status_code >= 400:
                    print(f"  Gemini ERROR {res.status_code}: {res.text[:300]}")
                    res.raise_for_status()
                data = res.json()
                cand = (data.get("candidates") or [{}])[0]
                parts = (cand.get("content") or {}).get("parts") or []
                content = "".join(p.get("text", "") for p in parts)
                um = data.get("usageMetadata", {})
                usage = {
                    "prompt_tokens": um.get("promptTokenCount", 0),
                    "completion_tokens": um.get("candidatesTokenCount", 0),
                    "total_tokens": um.get("totalTokenCount", 0),
                }
                finish = cand.get("finishReason", "unknown")  # STOP | MAX_TOKENS
                return content, {"usage": usage, "finish_reason": finish}
            except httpx.HTTPStatusError:
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                print(f"  Gemini network error (attempt {attempt}/{retries}): {type(e).__name__}")
                last_err = str(e)
                await asyncio.sleep(10)
    raise RuntimeError(f"Gemini API failed after {retries} retries. Last: {last_err}")


def get_api_key(provider: str) -> str:
    if provider == "glm":
        key = os.getenv("GLM_API_KEY") or settings.GLM_API_KEY
    elif provider == "groq":
        key = os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
    elif provider == "gemini":
        key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    elif provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY") or settings.OPENROUTER_API_KEY
    else:
        raise SystemExit(f"Unknown provider '{provider}'")
    if not key:
        raise SystemExit(f"API key for '{provider}' not set")
    return key


async def call_openrouter_raw(
    prompt: str,
    model: str,
    max_tokens: int,
    temperature: float,
    api_key: str,
    retries: int = 3,
) -> tuple[str, dict]:
    """Call OpenRouter (OpenAI-compatible) and return (content, usage/finish meta)."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "QA Test Case Generator Benchmark",
    }
    timeout = httpx.Timeout(420.0, connect=30.0)
    last_err = None
    for attempt in range(1, retries + 1):
        async with httpx.AsyncClient(timeout=timeout, verify=True) as client:
            try:
                # Hard cap each attempt (httpx read-timeout can fail to fire
                # when a server silently drops the stream).
                res = await asyncio.wait_for(
                    client.post("https://openrouter.ai/api/v1/chat/completions",
                                json=payload, headers=headers),
                    timeout=480.0,
                )
                if res.status_code in (408, 429, 500, 502, 503, 524):
                    print(f"  OpenRouter {res.status_code} (attempt {attempt}/{retries}), retry in 10s...")
                    last_err = f"{res.status_code}: {res.text[:200]}"
                    await asyncio.sleep(10)
                    continue
                if res.status_code >= 400:
                    print(f"  OpenRouter ERROR {res.status_code}: {res.text[:400]}")
                    res.raise_for_status()
                data = res.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content") or ""
                if not content.strip():
                    content = msg.get("reasoning") or ""
                usage = data.get("usage", {})
                finish = data["choices"][0].get("finish_reason", "unknown")
                # OpenRouter cost fields (per-request USD cost, if available)
                cost = data.get("cost") or {}
                return content, {"usage": usage, "finish_reason": finish, "cost": cost}
            except httpx.HTTPStatusError:
                raise
            except (httpx.RequestError, httpx.TimeoutException, asyncio.TimeoutError) as e:
                print(f"  OpenRouter network error (attempt {attempt}/{retries}): {type(e).__name__}")
                last_err = str(e)
                await asyncio.sleep(10)
    raise RuntimeError(f"OpenRouter failed after {retries} retries. Last: {last_err}")


async def call_provider_raw(provider: str, prompt: str, model: str,
                            max_tokens: int, temperature: float, api_key: str):
    if provider == "glm":
        return await call_glm_raw(prompt, model, max_tokens, temperature, api_key)
    if provider == "groq":
        return await call_groq_raw(prompt, model, max_tokens, temperature, api_key)
    if provider == "gemini":
        return await call_gemini_raw(prompt, model, max_tokens, temperature, api_key)
    if provider == "openrouter":
        return await call_openrouter_raw(prompt, model, max_tokens, temperature, api_key)
    raise SystemExit(f"Unknown provider '{provider}'")


def parse_tc_counts(content: str) -> dict:
    """Parse the JSON output and count test cases per category."""
    try:
        data = json.loads(content)
        return {
            "functional": len(data.get("functional", [])),
            "negative": len(data.get("negative", [])),
            "boundary": len(data.get("boundary", [])),
            "total": len(data.get("functional", []))
            + len(data.get("negative", []))
            + len(data.get("boundary", [])),
            "valid_json": True,
        }
    except Exception:
        # Try to salvage by counting tc_id occurrences
        import re

        f = len(re.findall(r"TC-F-\d+", content))
        n = len(re.findall(r"TC-N-\d+", content))
        b = len(re.findall(r"TC-B-\d+", content))
        return {
            "functional": f,
            "negative": n,
            "boundary": b,
            "total": f + n + b,
            "valid_json": False,
        }


async def main():
    parser = argparse.ArgumentParser(description="Benchmark multi-provider generation")
    parser.add_argument("document_id", nargs="?", type=int, default=13)
    parser.add_argument("--provider", choices=["glm", "groq", "gemini", "openrouter"], default="glm")
    parser.add_argument("--model", default=None,
                        help="Model name (defaults per provider: glm=glm-5-turbo, "
                             "groq=llama-3.3-70b-versatile, gemini=gemini-2.0-flash)")
    parser.add_argument("--target", type=int, default=60, help="target per functional/negative category")
    parser.add_argument("--target-boundary", type=int, default=50)
    parser.add_argument("--max-tokens", type=int, default=24576)
    parser.add_argument("--temperature", type=float, default=0.5)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--save-xlsx", type=str, default=None,
                        help="If set, save the LAST successful run's output to this .xlsx path")
    parser.add_argument("--parallel", action="store_true",
                        help="Use 3 parallel category-focused calls (functional/negative/boundary) instead of one single call")
    parser.add_argument("--target-f", type=int, default=None, help="Override functional target")
    parser.add_argument("--target-n", type=int, default=None, help="Override negative target")
    args = parser.parse_args()

    if args.model is None:
        args.model = DEFAULT_MODEL_BY_PROVIDER[args.provider]
    api_key = get_api_key(args.provider)

    title, doc_text = await load_document_text(args.document_id)
    print("=" * 70)
    print(f"{args.provider.upper()} GENERATION BENCHMARK")
    print("=" * 70)
    print(f"  Document : id={args.document_id} | {title}")
    print(f"  Doc size : {len(doc_text):,} chars")
    print(f"  Provider : {args.provider}")
    print(f"  Model    : {args.model}")
    print(f"  Target   : functional={args.target}, negative={args.target}, boundary={args.target_boundary}")
    print(f"  Max tokens: {args.max_tokens:,}")
    print(f"  Temperature: {args.temperature}")
    print(f"  Runs     : {args.runs}")
    print("=" * 70)

    results = []
    for run in range(1, args.runs + 1):
        print(f"\n--- Run {run}/{args.runs} ---")

        prompt = build_v8_full_generate_prompt(
            doc_text,
            target_functional=args.target,
            target_negative=args.target,
            target_boundary=args.target_boundary,
        )
        print(f"  Prompt length: {len(prompt):,} chars")

        t0 = time.perf_counter()
        if args.parallel:
            # ---- PARALLEL MODE: 3 category-focused calls concurrently ----
            cat_targets = {
                "functional": args.target_f if args.target_f else args.target,
                "negative": args.target_n if args.target_n else args.target,
                "boundary": args.target_boundary,
            }
            prompts = {
                cat: build_v8_category_prompt(cat, doc_text, requirement=None, target=t)
                for cat, t in cat_targets.items()
            }
            for cat, pr in prompts.items():
                print(f"  [{cat}] prompt: {len(pr):,} chars, target {cat_targets[cat]} TC")

            async def run_one(cat: str, pr: str):
                try:
                    return cat, await call_provider_raw(args.provider, pr, args.model, args.max_tokens, args.temperature, api_key)
                except Exception as e:
                    return cat, e

            outcomes = await asyncio.gather(
                run_one("functional", prompts["functional"]),
                run_one("negative", prompts["negative"]),
                run_one("boundary", prompts["boundary"]),
            )

            functional, negative, boundary = [], [], []
            total_pt = total_ct = 0
            total_cost = 0.0
            finish_reasons = []
            for cat, outcome in outcomes:
                if isinstance(outcome, Exception):
                    print(f"  [{cat}] FAILED: {type(outcome).__name__}: {str(outcome)[:200]}")
                    finish_reasons.append("error")
                    continue
                content_cat, meta_cat = outcome
                u = meta_cat["usage"]
                total_pt += u.get("prompt_tokens", 0)
                total_ct += u.get("completion_tokens", 0)
                # OpenRouter reports actual USD cost per request
                cost = meta_cat.get("cost") or {}
                req_cost = float(cost.get("total_cost") or cost.get("cost") or 0)
                total_cost += req_cost
                finish_reasons.append(meta_cat["finish_reason"])
                # Parse JSON array of TCs (salvage if truncated)
                try:
                    arr = json.loads(content_cat)
                    if isinstance(arr, dict):
                        arr = arr.get(cat, [])
                    if not isinstance(arr, list):
                        arr = []
                except Exception:
                    from app.pipeline.postprocessor.parser import salvage_tc_array
                    arr = salvage_tc_array(content_cat)
                    print(f"  [{cat}] JSON truncated → salvaged {len(arr)} TC")
                if cat == "functional":
                    functional = arr
                elif cat == "negative":
                    negative = arr
                else:
                    boundary = arr
                cost_str = f", ${req_cost:.4f}" if req_cost else ""
                print(f"  [{cat}] {meta_cat['finish_reason']}: {len(arr)} TC, "
                      f"{u.get('completion_tokens',0):,} completion tokens{cost_str}")

            if total_cost:
                print(f"  💵 Actual cost (OpenRouter): ${total_cost:.4f}")

            elapsed = time.perf_counter() - t0
            counts = {
                "functional": len(functional),
                "negative": len(negative),
                "boundary": len(boundary),
                "total": len(functional) + len(negative) + len(boundary),
                "valid_json": True,  # per-category arrays already parsed
            }
            usage = {
                "prompt_tokens": total_pt,
                "completion_tokens": total_ct,
                "total_tokens": total_pt + total_ct,
            }
            finish = ",".join(set(finish_reasons))
            content = json.dumps({
                "summary": {
                    "id": "REQ-001",
                    "nama": title,
                    "deskripsi": f"Benchmark suite — {len(functional)} functional, {len(negative)} negative, {len(boundary)} boundary test case.",
                    "prioritas": "Medium",
                    "kategori": "Benchmark",
                    "fitur_kunci": [],
                },
                "functional": functional,
                "negative": negative,
                "boundary": boundary,
                "risk": {"level": "Benchmark", "notes": ["Risk assessment tidak digenerate pada mode benchmark."]},
            }, ensure_ascii=False)
            pt, ct, tt = total_pt, total_ct, total_pt + total_ct
        else:
            try:
                content, meta = await call_provider_raw(
                    args.provider, prompt, args.model, args.max_tokens, args.temperature, api_key
                )
            except Exception as e:
                print(f"  ERROR: {type(e).__name__}: {str(e)[:300]}")
                continue
            elapsed = time.perf_counter() - t0

            usage = meta["usage"]
            finish = meta["finish_reason"]
            counts = parse_tc_counts(content)

            pt = usage.get("prompt_tokens", 0)
            ct = usage.get("completion_tokens", 0)
            tt = usage.get("total_tokens", pt + ct)

        result = {
            "run": run,
            "time_sec": round(elapsed, 1),
            "prompt_tokens": pt,
            "completion_tokens": ct,
            "total_tokens": tt,
            "finish_reason": finish,
            "output_chars": len(content),
            **counts,
        }
        results.append(result)

        print(f"  ⏱  Time          : {elapsed:.1f}s ({elapsed/60:.1f} min)")
        print(f"  🔤 Tokens        : prompt={pt:,} | completion={ct:,} | total={tt:,}")
        print(f"  ✋ Finish reason : {finish}")
        print(f"  📦 Output        : {len(content):,} chars | valid_json={counts['valid_json']}")
        print(f"  🧪 Test cases    : functional={counts['functional']} | negative={counts['negative']} | boundary={counts['boundary']} | TOTAL={counts['total']}")

        # Save to xlsx (only when output is valid JSON + finish=stop)
        if args.save_xlsx and counts["valid_json"]:
            try:
                parsed = json.loads(content)
                result_for_excel = {
                    "summary": parsed.get("summary", {}),
                    "functional": parsed.get("functional", []),
                    "negative": parsed.get("negative", []),
                    "boundary": parsed.get("boundary", []),
                    "risk": parsed.get("risk", {}),
                    "metadata": {"pipeline": "v8-parallel-benchmark"},
                }
                requirement = (parsed.get("summary") or {}).get("nama") or title
                xlsx_bytes = excel_exporter.generate_excel(result_for_excel, requirement, args.model)
                out_path = args.save_xlsx
                if args.runs > 1:
                    # append run index for multi-run
                    base, ext = os.path.splitext(out_path)
                    out_path = f"{base}_run{run}{ext}"
                with open(out_path, "wb") as f:
                    f.write(xlsx_bytes)
                print(f"  📄 Excel saved   : {out_path} ({len(xlsx_bytes):,} bytes)")
            except Exception as e:
                print(f"  ⚠️  Excel save failed: {type(e).__name__}: {e}")

    # Summary
    if results:
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        n = len(results)
        avg_time = sum(r["time_sec"] for r in results) / n
        avg_pt = sum(r["prompt_tokens"] for r in results) / n
        avg_ct = sum(r["completion_tokens"] for r in results) / n
        avg_tt = sum(r["total_tokens"] for r in results) / n
        avg_tc = sum(r["total"] for r in results) / n
        print(f"  Avg time            : {avg_time:.1f}s ({avg_time/60:.1f} min)")
        print(f"  Avg prompt tokens   : {avg_pt:,.0f}")
        print(f"  Avg completion tokens: {avg_ct:,.0f}")
        print(f"  Avg total tokens    : {avg_tt:,.0f}")
        print(f"  Avg test cases      : {avg_tc:.0f}")
        if avg_tc > 0:
            print(f"  Tokens per TC       : {avg_tt/avg_tc:,.0f}")
            print(f"  Time per TC         : {avg_time/avg_tc:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
