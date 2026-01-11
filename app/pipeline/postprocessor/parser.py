import json
import re
from sys import prefix


def normalize_string(v):
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    return str(v).strip()


def normalize_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [normalize_string(x) for x in v if normalize_string(x)]
    return [normalize_string(v)]


def extract_json_block(text):
    if not text:
        return None
    match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", text)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except Exception:
        return None


def parse_any_json(text):
    if not text or not isinstance(text, str):
        return None

    # Ambil JSON dari ```json ... ```
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)

    # Fallback: ambil {...} atau [...]
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        text = match.group(1)

    try:
        return json.loads(text)
    except Exception as e:
        print("parse_any_json FAILED:", e)
        return None




def derive_title(tc):
    for k in ["title", "nama", "name", "description", "deskripsi"]:
        v = tc.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()[:120]

    steps = tc.get("steps", [])
    if isinstance(steps, list) and steps:
        return normalize_string(steps[0])[:120]

    return "Untitled Test Case"


def normalize_expected(e):
    if isinstance(e, str):
        return e.strip()

    if isinstance(e, dict):
        for k in ["message", "error", "detail", "status"]:
            if k in e and isinstance(e[k], str):
                return e[k]

        return " | ".join(f"{k}: {v}" for k, v in e.items())

    return str(e)


def parse_testcases_json(raw_json, prefix="TC-X"):
    if not isinstance(raw_json, list):
        return []

    normalized = []
    idx = 1

    for tc in raw_json:
        if not isinstance(tc, dict):
            continue

        ntc = normalize_tc(tc, prefix, idx)
        if ntc:
            normalized.append(ntc)
            idx += 1

    return normalized


def flatten_step(step):
    if isinstance(step, str):
        return step.strip()

    if isinstance(step, dict):
        if "description" in step:
            return step["description"]

        return " | ".join(f"{k}: {v}" for k, v in step.items())

    return str(step)

def flatten_expected(e):
    if isinstance(e, str):
        return e.strip()

    if isinstance(e, dict):
        if "message" in e:
            return e["message"]

        return " | ".join(f"{k}: {v}" for k, v in e.items())

    return str(e)




def normalize_tc(tc, prefix, idx):
    # Use derive_title to intelligently extract title from various fields
    title = derive_title(tc)

    return {
        "tc_id": f"{prefix}-{idx:03d}",
        "title": title,
        "preconditions": tc.get("preconditions", []),
        "steps": tc.get("steps", []),
        "expected_result": tc.get("expected_result", []),
    }


def normalize_steps(steps):
    result = []
    for s in steps or []:
        if isinstance(s, dict):
            result.append(s.get("description") or str(s))
        else:
            result.append(str(s))
    return result

def normalize_expected(raw_expected):
    if not isinstance(raw_expected, list):
        return []

    return [str(e) for e in raw_expected]