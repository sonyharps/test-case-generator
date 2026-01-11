def build_tc_extractor_prompt(text: str) -> str:
    return f"""
Kamu adalah mesin konversi TEKS → JSON.

ATURAN KERAS:
- Output HARUS JSON VALID
- TIDAK BOLEH ADA teks penjelasan
- TIDAK BOLEH ada markdown
- TIDAK BOLEH ada komentar
- TIDAK BOLEH ada prefix / suffix
- LANGSUNG array JSON

FORMAT WAJIB:
[
  {{
    "tc_id": "",
    "title": "",
    "preconditions": ["..."],
    "steps": ["..."],
    "expected_result": ["..."]
  }}
]

KONDISI:
- steps HARUS array of STRING (bukan object)
- expected_result HARUS array of STRING
- Jika data tidak ada, isi dengan kalimat yang masuk akal

TEKS SUMBER:
{text}

OUTPUT (JSON SAJA):
"""
