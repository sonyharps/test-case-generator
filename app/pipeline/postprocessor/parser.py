import json
import re


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


def parse_any_json(raw):
    if raw is None:
        return {}
    if isinstance(raw, (dict, list)):
        return raw

    try:
        return json.loads(raw)
    except Exception:
        extracted = extract_json_block(raw)
        return extracted if extracted is not None else {}


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


def parse_testcases_json(raw, prefix="TC"):
    parsed = parse_any_json(raw)
    if not parsed:
        return []

    if isinstance(parsed, dict):
        testcases = parsed.get("testcases") or parsed.get("cases") or []
    elif isinstance(parsed, list):
        testcases = parsed
    else:
        return []

    results = []

    for i, tc in enumerate(testcases, start=1):
        if not isinstance(tc, dict):
            continue

        title = derive_title(tc)

        preconditions = normalize_list(tc.get("preconditions"))
        if not preconditions:
            preconditions = [
                "User berada pada halaman login",
                "User memiliki akun terdaftar"
            ]

        steps = []
        raw_steps = tc.get("steps", [])
        if isinstance(raw_steps, list):
            for s in raw_steps:
                steps.append(flatten_step(s))
        elif isinstance(raw_steps, str):
            steps.append(raw_steps)

        if not steps:
            steps = ["Lakukan aksi sesuai skenario"]

        expected_raw = tc.get("expected_result") or tc.get("expected") or []
        expected = normalize_list([flatten_expected(e) for e in expected_raw])

        if not expected:
            expected = ["Sistem merespons sesuai ekspektasi"]

        results.append({
            "tc_id": tc.get("tc_id") or f"{prefix}-{i:03}",
            "title": title,
            "preconditions": preconditions,
            "steps": steps,
            "expected_result": expected
        })

    return results

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
