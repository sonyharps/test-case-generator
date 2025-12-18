import json
import re

# ================================================================
# GENERIC JSON EXTRACTOR
# ================================================================
def parse_any_json(text: str):
    """Extract the first valid JSON object or array from noisy LLM output."""
    if not text:
        return {}

    # Remove markdown fences
    cleaned = (
        text.replace("```json", "")
            .replace("```", "")
            .strip()
    )

    # Remove non-ASCII / weird unicode chars (root cause summary noise)
    cleaned = re.sub(r"[^\x20-\x7E\n\r\t{}[\],:\"0-9A-Za-z._-]", "", cleaned)

    # First attempt: direct JSON load
    try:
        return json.loads(cleaned)
    except:
        pass

    # Second attempt: find JSON region
    json_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass

    # Failed → return safe empty dict
    return {}


# ================================================================
# ENTERPRISE TEST CASE PARSER
# ================================================================
def normalize_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return []

def normalize_string(value):
    if value is None:
        return ""
    return str(value)

def fix_testcase_structure(tc: dict, default_prefix="TC-X"):
    return {
        "tc_id": normalize_string(tc.get("tc_id", f"{default_prefix}-XXX")),
        "title": normalize_string(tc.get("title")),
        "preconditions": normalize_list(tc.get("preconditions")),
        "steps": normalize_list(tc.get("steps")),
        "expected_result": normalize_list(tc.get("expected_result")),
        "boundary_type": normalize_string(tc.get("boundary_type"))
            if "boundary_type" in tc else "",
    }

def parse_testcases_json(text: str, prefix="TC"):
    raw = parse_any_json(text)

    if isinstance(raw, dict):
        raw = [raw]

    if not isinstance(raw, list):
        return []

    cleaned = []
    counter = 1

    for item in raw:
        tc = fix_testcase_structure(item, default_prefix=prefix)

        # Auto-generate ID if LLM didn't supply
        if tc["tc_id"] in ["", None, f"{prefix}-XXX"]:
            tc["tc_id"] = f"{prefix}-{counter:03d}"

        cleaned.append(tc)
        counter += 1

    return cleaned


def extract_partial_json(text: str):
    """
    Extract JSON even if it's partially truncated.
    Attempts closing braces/brackets automatically.
    """
    cleaned = text.replace("```json", "").replace("```", "").strip()

    # Cari posisi awal JSON
    start = cleaned.find("{")
    if start == -1:
        return {}

    snippet = cleaned[start:]

    # Coba menambahkan kurung penutup sampai valid
    for extra in ["}", "}}", "}}}", "]", "]]", "]]]"]:
        try:
            return json.loads(snippet + extra)
        except:
            pass

    # Last fallback: return empty
    return {}
