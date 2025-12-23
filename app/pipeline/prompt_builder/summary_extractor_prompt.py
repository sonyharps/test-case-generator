def build_summary_extractor_prompt(raw_text: str):
    return f"""
Anda adalah sistem ekstraksi requirement profesional.

ATURAN KERAS:
1. Output HARUS JSON VALID
2. Tidak boleh markdown
3. Tidak boleh teks tambahan
4. HARUS mulai {{ dan berakhir }}

FORMAT:
{{
  "kriteria": [
    {{
      "id": "REQ-001",
      "nama": "",
      "deskripsi": "",
      "prioritas": "",
      "kategori": ""
    }}
  ]
}}

SUMBER TEKS:
\"\"\"
{raw_text}
\"\"\"

HASILKAN JSON SEKARANG.
"""
