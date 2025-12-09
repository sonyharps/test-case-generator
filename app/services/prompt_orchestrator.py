# app/services/prompt_orchestrator.py

def functional_json_prompt(requirement: str):
    return f"""
Kamu adalah Senior QA Engineer.
Buat minimal 5 test case fungsional dalam format JSON valid (array of objects).
REQUIREMENT:
{requirement}
FORMAT:
[
  {{
    "tc_id":"TC-001",
    "title":"string",
    "preconditions":["string"],
    "steps":["string"],
    "expected_result":["string"]
  }},
  ...
]
Hanya tampilkan JSON final saja.
"""

def negative_json_prompt(requirement: str):
    return f"""
Kamu adalah Senior QA Engineer.
Buat minimal 5 test case NEGATIF dalam JSON valid (array of objects) dengan tc_id NEG-001, NEG-002, ...
REQUIREMENT:
{requirement}
FORMAT: (sama schema seperti functional but ids NEG-001 dst)
Hanya tampilkan JSON final saja.
"""

def boundary_json_prompt(requirement: str):
    return f"""
Kamu adalah Senior QA Engineer.
Buat minimal 5 test case BOUNDARY / EDGE CASE dalam JSON valid (array of objects) dengan tc_id BND-001, BND-002, ...
Contoh: min length, max length, empty input, concurrency, large payload.
REQUIREMENT:
{requirement}
FORMAT: (sama schema)
Hanya tampilkan JSON final saja.
"""

def summary_prompt(requirement: str, functional_count:int, negative_count:int, boundary_count:int):
    return f"""
Buat ringkasan singkat 2-3 kalimat dari hasil generasi test case berikut:
Requirement: {requirement}
Functional count: {functional_count}
Negative count: {negative_count}
Boundary count: {boundary_count}

Berikan juga 3 poin highlight risiko (singkat).
Hanya tampilkan ringkasan dan 3 poin, tanpa JSON.
"""
