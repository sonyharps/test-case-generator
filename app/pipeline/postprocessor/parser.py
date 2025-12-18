import json
import re

# ================================================================
# GENERIC JSON EXTRACTOR
# ================================================================
def parse_any_json(text: str):
    """Extract first valid JSON object/array from noisy LLM output."""
    if not text:
        return {}

    cleaned = (
        text.replace("```json", "")
            .replace("```", "")
            .strip()
    )
    # ============================================
    # ASCII Sanitizer (fix summary unicode issue)
    # ============================================
    cleaned = cleaned.encode("ascii", "ignore").decode()

    # Try direct load
    try:
        return json.loads(cleaned)
    except:
        pass

    # Try extract JSON
    json_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass

    return {}

# ================================================================
# ENTERPRISE TEST CASE PARSER
# ================================================================
def normalize_list(value):
    """Ensure a field is always a list"""
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
    """
    Guarantee test case structure always valid.
    Auto-fix missing fields & normalize list fields.
    """
    return {
        "tc_id": normalize_string(tc.get("tc_id", f"{default_prefix}-XXX")),
        "title": normalize_string(tc.get("title")),
        "preconditions": normalize_list(tc.get("preconditions")),
        "steps": normalize_list(tc.get("steps")),
        "expected_result": normalize_list(tc.get("expected_result")),
        # Boundary only (optional)
        "boundary_type": normalize_string(tc.get("boundary_type"))
            if "boundary_type" in tc else "",
    }

def parse_testcases_json(text: str, prefix="TC"):
    """
    Handle noisy LLM JSON output and return sanitized list of test cases.
    """
    raw = parse_any_json(text)

    # Case: single object → convert to list
    if isinstance(raw, dict):
        raw = [raw]

    # Case: bad data → empty list
    if not isinstance(raw, list):
        return []

    cleaned = []
    counter = 1

    for item in raw:
        tc = fix_testcase_structure(item, default_prefix=prefix)
        
        # Auto-generate TC ID if missing
        if "TC-" in prefix or prefix in tc["tc_id"]:
            pass
        else:
            tc["tc_id"] = f"{prefix}-{counter:03d}"

        cleaned.append(tc)
        counter += 1

    return cleaned
