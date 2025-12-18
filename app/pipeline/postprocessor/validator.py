# app/pipeline/postprocessor/validator.py

def validate_testcases(items):
    if not isinstance(items, list):
        return False

    for tc in items:
        if "tc_id" not in tc:
            tc["tc_id"] = "UNKNOWN"
        if "title" not in tc:
            tc["title"] = "Untitled"

    return True
