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


def salvage_tc_array(text):
    """Salvage complete test-case objects from TRUNCATED/malformed JSON.

    Long generations sometimes hit the max_tokens limit mid-array, and the
    output may be a bare array, an object-wrapped array
    (``{"negative": [ {...}, {...``), or carry stray text. Standard
    json.loads fails on all of those. This walks brace depth and extracts
    every COMPLETE balanced {...} block ANYWHERE in the text, keeping only
    objects that look like test cases (have a tc_id or title key). Returns
    a list of dicts (possibly empty).
    """
    if not text or not isinstance(text, str):
        return []

    # Remove markdown fence markers (keep surrounding content)
    text = re.sub(r"```(?:json)?", "", text)

    objects = []
    stack = []  # indexes of '{' positions
    in_string = False
    escape = False

    for i, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            stack.append(i)
        elif ch == "}":
            if stack:
                start = stack.pop()
                chunk = text[start : i + 1]
                try:
                    obj = json.loads(chunk)
                    # Keep only test-case objects; wrapper objects
                    # ({"negative": [...]}, summary, risk) lack tc_id.
                    if isinstance(obj, dict) and "tc_id" in obj:
                        objects.append(obj)
                except Exception:
                    pass

    return objects




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

    # ISO/IEC/IEEE 29119-3 fields — all optional, default sensibly for backward compat
    priority = tc.get("priority") or tc.get("prioritas")
    if priority:
        priority = normalize_string(priority).upper()
        # Normalize P0/P1/P2/P3 / Critical/Major/Minor etc.
        valid = {"P0", "P1", "P2", "P3", "CRITICAL", "HIGH", "MAJOR", "MEDIUM", "LOW", "MINOR"}
        if priority.upper() not in valid:
            priority = "P2"  # default to important

    module = tc.get("module") or tc.get("area") or tc.get("fitur")
    if module:
        module = normalize_string(module)

    test_data = tc.get("test_data") or tc.get("testdata") or tc.get("data")
    postconditions = tc.get("postconditions") or tc.get("post_conditions")

    return {
        "tc_id": f"{prefix}-{idx:03d}",
        "title": title,
        "priority": priority or "P2",
        "module": module or "",
        "preconditions": normalize_list(tc.get("preconditions")),
        "test_data": normalize_list(test_data),
        "steps": normalize_list(tc.get("steps")),
        "expected_result": normalize_list(tc.get("expected_result")),
        "postconditions": normalize_list(postconditions),
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