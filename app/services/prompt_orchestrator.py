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

Buat 5 test case NEGATIF dalam format JSON VALID,
dengan schema WAJIB seperti berikut:

[
  {{
    "tc_id": "NEG-001",
    "title": "string",
    "preconditions": ["string"],
    "steps": ["string"],
    "expected_result": ["string"]
  }}
]

Pastikan:
- MENGGUNAKAN ARRAY OF OBJECTS
- expected_result HARUS dalam array, bukan string
- Gunakan prefix NEG-001, NEG-002, dst
- Jangan gunakan atribut selain yang muncul di schema

Requirement:
{requirement}

Hanya tampilkan JSON final saja.
"""


def boundary_json_prompt(requirement: str):
    return f"""
Kamu adalah Senior QA Engineer.

Buat 5 test case BOUNDARY / EDGE CASE dalam JSON VALID.
Schema WAJIB seperti berikut:

[
  {{
    "tc_id": "BND-001",
    "title": "string",
    "preconditions": ["string"],
    "steps": ["string"],
    "expected_result": ["string"]
  }}
]

Catatan:
- Fokus pada batas minimal/maksimal input
- Contoh: min length, max length, empty input, extremely long input
- expected_result harus array
- Gunakan prefix BND-001, BND-002, dst

Requirement:
{requirement}

Hanya tampilkan JSON final saja.
"""

def summary_prompt(functional: list, negative: list, boundary: list):
    return f"""
Buat ringkasan test case berikut dalam bahasa Indonesia.

Format ringkasan:
- Total jumlah test case per kategori
- Tujuan test secara umum
- Risiko potensial yang perlu diperhatikan (3 poin)
- Area sistem yang paling terdampak

Data test case:
Functional: {functional}
Negative: {negative}
Boundary: {boundary}

Hanya kembalikan ringkasan dalam bentuk paragraf, jangan beri JSON.
"""

def risk_prompt(functional: list, negative: list, boundary: list):
    return f"""
Analisis risiko berdasarkan test case berikut:

Functional: {functional}
Negative: {negative}
Boundary: {boundary}

Buat output JSON dengan format:

{
  "level": "low | medium | high",
  "notes": ["risiko 1", "risiko 2", "risiko 3"]
}

Pastikan JSON valid.
"""

