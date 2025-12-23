# app/pipeline/prompt_builder/generation_prompt.py

import json

def build_generation_prompt(req: str, reasoning: dict, planning: dict):
    reasoning_str = json.dumps(reasoning, ensure_ascii=False)
    planning_str = json.dumps(planning, ensure_ascii=False)

    return (
        "Anda adalah Senior QA Engineer.\n"
        "Bangun test suite lengkap berbasis requirement, reasoning, dan rencana testing berikut.\n\n"

        "REQUIREMENT:\n"
        f"{req}\n\n"

        "REASONING:\n"
        f"{reasoning_str}\n\n"

        "PLANNING:\n"
        f"{planning_str}\n\n"

        "OUTPUTKAN JSON FINAL DENGAN STRUKTUR:\n"
        "{\n"
        '  "summary": {\n'
        '      "id": "REQ-001",\n'
        '      "nama": "",\n'
        '      "deskripsi": "",\n'
        '      "prioritas": "",\n'
        '      "kategori": "",\n'
        '      "fitur_kunci": []\n'
        "  },\n"
        '  "functional": [],\n'
        '  "negative": [],\n'
        '  "boundary": []\n'
        "}\n\n"

        "SETIAP TEST CASE HARUS BERFORMAT:\n"
        "{\n"
        '  "tc_id": "",\n'
        '  "title": "",\n'
        '  "preconditions": [],\n'
        '  "steps": [],\n'
        '  "expected_result": []\n'
        "}\n\n"

        "WAJIB JSON VALID. TANPA MARKDOWN. TANPA BACKTICK."
    )
