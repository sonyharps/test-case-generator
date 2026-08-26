"""
V8 Summary Prompt — lightweight parallel 4th call.

While the three category calls (functional/negative/boundary) generate the
test cases, this small call reads the SAME document and produces the report
metadata: requirement summary (nama, deskripsi, prioritas, kategori, fitur
kunci) + risk assessment. Output is tiny (~500 tokens), so it adds no
perceptible wall-clock time when run concurrently with the category calls.
"""

from typing import Optional

from app.pipeline.prompt_builder.v8_full_generate_prompt import _truncate_doc


def build_v8_summary_prompt(
    document_text: str,
    requirement: Optional[str] = None,
) -> str:
    focus_block = ""
    if requirement and requirement.strip():
        focus_block = f"\nFOKUS REQUIREMENT TAMBAHAN:\n{requirement.strip()}\n"

    return f"""Anda adalah Principal QA Engineer. Baca dokumen sumber berikut dan hasilkan RINGKASAN REQUIREMENT + PENILAIAN RISIKO untuk report test case.

DOKUMEN SUMBER:
---
{_truncate_doc(document_text, max_chars=30000)}
---
{focus_block}
ATURAN OUTPUT (KERAS):
- Output HARUS JSON MURNI dalam BAHASA INDONESIA. Tidak boleh markdown atau teks di luar JSON.

FORMAT WAJIB:
{{
  "summary": {{
    "id": "REQ-001",
    "nama": "judul fitur/requirement utama dari dokumen",
    "deskripsi": "ringkasan 1-2 kalimat apa yang diuji, merujuk isi dokumen",
    "prioritas": "High | Medium | Low",
    "kategori": "domain/klasifikasi (contoh: Banking - Credit Screening)",
    "fitur_kunci": ["fitur 1", "fitur 2", "fitur 3"]
  }},
  "risk": {{
    "level": "Low | Medium | High",
    "notes": ["catatan risiko utama terkait fitur di dokumen"]
  }}
}}

OUTPUT JSON SAJA.
"""
