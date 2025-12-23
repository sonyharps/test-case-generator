def build_tc_extractor_prompt(raw_text: str):
    return f"""
Anda adalah sistem konversi test case ke JSON.

ATURAN KERAS (TIDAK BOLEH DILANGGAR):
1. Output HARUS JSON ARRAY
2. Tidak boleh teks, judul, bullet, simbol, markdown
3. Tidak boleh string di luar JSON
4. Setiap test case HARUS lengkap
5. Jika informasi tidak ada, isi string kosong ""

FORMAT WAJIB:
[
  {{
    "tc_id": "TC-X-001",
    "title": "",
    "preconditions": [],
    "steps": [],
    "expected_result": []
  }}
]

KONVERSI TEKS BERIKUT:
\"\"\"
{raw_text}
\"\"\"

HASILKAN JSON SAJA. MULAI DENGAN '[' DAN AKHIRI DENGAN ']'.
"""
