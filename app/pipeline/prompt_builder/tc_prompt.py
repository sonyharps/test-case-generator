def build_functional_prompt(success_space):
    return f"""
Anda adalah Senior QA Engineer.

Berdasarkan daftar skenario berikut:
{success_space}

Buat TEST CASE FUNGSIONAL.

WAJIB output JSON ARRAY.
Setiap item WAJIB punya field:
- tc_id
- title
- preconditions (array string)
- steps (array string)
- expected_result (array string)

ATURAN:
- steps HARUS kalimat manusia (bukan JSON)
- expected_result HARUS deskriptif
- title HARUS jelas & unik

FORMAT WAJIB:
[
  {{
    "tc_id": "TC-F-001",
    "title": "Judul test case",
    "preconditions": [],
    "steps": [],
    "expected_result": []
  }}
]

DILARANG:
- field lain
- nested object
- markdown
- teks di luar JSON
"""
