# app/pipeline/prompt_builder/planning_prompt.py

import json

def build_planning_prompt(req: str, reasoning_json: dict):
    reasoning = json.dumps(reasoning_json, ensure_ascii=False)

    return (
        "Anda adalah QA Test Architect.\n"
        "Buat rencana test komprehensif berdasarkan requirement dan hasil analisis.\n\n"

        "REQUIREMENT:\n"
        f"{req}\n\n"

        "ANALISIS (REASONING):\n"
        f"{reasoning}\n\n"

        "OUTPUTKAN JSON VALID TANPA MARKDOWN:\n"
        "{\n"
        '  "functional_groups": [],\n'
        '  "negative_patterns": [],\n'
        '  "boundary_targets": [],\n'
        '  "risk_map": [],\n'
        '  "test_overview": ""\n'
        "}\n\n"

        "WAJIB JSON VALID. Hanya JSON, tanpa penjelasan."
    )
