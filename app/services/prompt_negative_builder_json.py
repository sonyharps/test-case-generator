def build_negative_json_prompt(requirement: str):
    return f"""
Kamu adalah Senior QA Engineer.

Buat **minimal 5 test case NEGATIF** dalam format **JSON valid**.

-----------------------------------------------------
REQUIREMENT:
{requirement}
-----------------------------------------------------

### FORMAT OUTPUT (WAJIB JSON VALID)

[
  {{
    "tc_id": "NEG-001",
    "title": "string",
    "preconditions": ["string"],
    "steps": ["string"],
    "expected_result": ["string"]
  }},
  ...
]

### ATURAN KETAT:
- Fokus pada skenario error, invalid input, edge case, constraint violation.
- Output HARUS JSON VALID tanpa teks tambahan.
- Gunakan Bahasa Indonesia formal.
- tc_id harus berurutan: NEG-001, NEG-002, NEG-003, ...
- steps & expected_result berupa list of strings.
- Jangan membuat paragraf atau komentar.

Hanya tampilkan JSON final.
"""
