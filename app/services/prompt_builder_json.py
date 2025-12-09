def build_tc_json_prompt(requirement: str):
    return f"""
Kamu adalah Senior QA Engineer.

Buat **minimal 5 test case fungsional** dalam format **JSON valid**.

-----------------------------------------------------
REQUIREMENT:
{requirement}
-----------------------------------------------------

### FORMAT OUTPUT (WAJIB JSON VALID)
Output HANYA berupa JSON array seperti ini:

[
  {{
    "tc_id": "TC-001",
    "title": "string",
    "preconditions": ["string"],
    "steps": ["string"],
    "expected_result": ["string"]
  }},
  ...
]

### ATURAN KETAT:
- TIDAK BOLEH ada teks di luar JSON (tidak boleh ada penjelasan, catatan, paragraf).
- JSON harus VALID (bisa di-parse Python).
- Gunakan Bahasa Indonesia formal.
- tc_id harus berurutan: TC-001, TC-002, ...
- steps & expected_result harus berupa array of string.

Hanya tampilkan JSON final saja.
"""
