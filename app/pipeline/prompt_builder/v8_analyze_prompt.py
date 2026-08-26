"""
V8 Analyze Prompt — Document-driven deep analysis (Phase 2 refactor).

Unlike v7's two separate summary + test_space calls, this single prompt feeds
the FULL source document (PRD, user story, etc.) to a powerful model and asks
it to produce a combined analysis: a requirement summary AND a rich,
exhaustive test space (many scenarios per bucket).
"""

from typing import Optional


def build_v8_analyze_prompt(
    document_text: str,
    requirement: Optional[str] = None,
    target_success: int = 10,
    target_failure: int = 10,
    target_boundary: int = 15,
) -> str:
    """Build the V8 analysis prompt.

    Args:
        document_text: The FULL source document text (PRD/user story/etc.).
        requirement: Optional focus requirement (free-text override or supplement).
        target_success: Minimum success scenarios to demand.
        target_failure: Minimum failure scenarios to demand.
        target_boundary: Minimum boundary scenarios to demand.

    Returns:
        The analysis prompt string.
    """
    focus_block = ""
    if requirement and requirement.strip():
        focus_block = f"""
FOKUS REQUIREMENT TAMBAHAN (prioritaskan ini):
{requirement.strip()}
"""

    return f"""
Anda adalah Principal QA Engineer dengan pengalaman 15+ tahun di software testing.

TUGAS UTAMA:
Baca SECARA MENYELURUH dokumen sumber berikut (PRD / User Story / Spec), pahami setiap fitur, alur, aturan bisnis, dan edge case, lalu hasilkan ANALISIS QA yang komprehensif dalam format JSON MURNI.

DOKUMEN SUMBER:
---
{document_text}
---
{focus_block}
INSTRUKSI ANALISIS:
1. Identifikasi SEMUA fitur/fungsi yang bisa diuji dari dokumen di atas.
2. Pikirkan dari sudut pandang pengguna akhir, admin, integrasi sistem, keamanan, dan performa.
3. Untuk setiap fitur, bayangkan: alur normal (happy path), alur gagal (error/invalid input), dan batas (boundary/extreme value).
4. Hasilkan test scenario yang BANYAK, BERAGAM, dan SPECIFIC ke konteks dokumen (bukan generic).

ATURAN KERAS (WAJIB):
- Output HARUS JSON MURNI. TIDAK BOLEH markdown, tidak boleh teks di luar JSON, tidak boleh komentar.
- Setiap scenario HARUS spesifik ke dokumen sumber (sebutkan fitur/konteks konkret).

FORMAT WAJIB:

{{
  "summary": {{
    "id": "REQ-001",
    "nama": "string - judul fitur/requirement utama dari dokumen",
    "deskripsi": "string - ringkasan singkat apa yang diuji, merujuk isi dokumen",
    "prioritas": "High | Medium | Low",
    "kategori": "string - domain/klasifikasi (e.g. E-commerce, Auth, Payment)",
    "fitur_kunci": ["string", "string", "..."] 
  }},
  "test_space": {{
    "success": [
      {{"scenario": "string - spesifik ke dokumen", "goal": "string - apa yang divalidasi"}}
    ],
    "failure": [
      {{"scenario": "string", "goal": "string"}}
    ],
    "boundary": [
      {{"scenario": "string", "goal": "string"}}
    ]
  }}
}}

TARGET VOLUME (MINIMAL — silakan lebihi jika dokumen memungkinkan):
- success: {target_success} item (alur normal & happy path tiap fitur)
- failure: {target_failure} item (error handling, invalid input, akses tidak sah)
- boundary: {target_boundary} item (min/max, empty, edge case, limit sistem)

OUTPUT JSON SAJA.
"""
