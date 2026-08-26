"""
V8 Generate Prompt — Powerful single-pass test case generation (Phase 2 refactor).

Replaces v7's two-call pattern (generate raw + tc_extractor) with ONE call that
emits clean structured JSON directly. Designed for powerful models (Gemini Flash,
Kimi K2, GPT-5) that can produce valid JSON in a single pass when given a strict
schema and the full document context.
"""

from typing import List, Optional

TEST_TYPE_LABELS = {
    "functional": ("TEST CASE FUNGSIONAL", "TC-F", "alur normal/happy path dari setiap skenario sukses"),
    "negative": ("TEST CASE NEGATIVE", "TC-N", "error handling, invalid input, dan kondisi gagal"),
    "boundary": ("TEST CASE BOUNDARY", "TC-B", "nilai batas, ekstrem, limit, dan edge case"),
}


def _truncate_doc(document_text: str, max_chars: int = 20000) -> str:
    """Truncate document to a safe size for the prompt window."""
    if len(document_text) <= max_chars:
        return document_text
    return document_text[:max_chars] + "\n\n[...dokumen dipotong karena panjang...]"


def build_v8_generate_prompt(
    test_type: str,
    scenarios: List[dict],
    document_text: Optional[str] = None,
    requirement: Optional[str] = None,
    target_per_scenario: int = 2,
) -> str:
    """Build the V8 single-pass test case generation prompt.

    Args:
        test_type: One of "functional", "negative", "boundary".
        scenarios: The scenario list for this type (from the analyze step).
        document_text: Optional full source document for context anchoring.
        requirement: Optional focus requirement text.
        target_per_scenario: How many test cases to produce per scenario (drives volume).

    Returns:
        The generation prompt string.
    """
    if test_type not in TEST_TYPE_LABELS:
        raise ValueError(f"Unknown test_type: {test_type}. Must be one of {list(TEST_TYPE_LABELS)}")

    label, prefix, focus_desc = TEST_TYPE_LABELS[test_type]
    doc_block = ""
    if document_text and document_text.strip():
        doc_block = f"""
KONTEKS DOKUMEN SUMBER (rujukan untuk detail langkah & expected result):
---
{_truncate_doc(document_text)}
---
"""
    focus_req_block = ""
    if requirement and requirement.strip():
        focus_req_block = f"\nFOKUS REQUIREMENT: {requirement.strip()}\n"

    # Render scenarios compactly
    scenarios_render = "\n".join(
        f"  {i+1}. Skenario: {s.get('scenario', '')} | Tujuan: {s.get('goal', '')}"
        for i, s in enumerate(scenarios)
        if s.get("scenario")
    )

    return f"""
Anda adalah Senior QA Engineer. Buat {label} ({focus_desc}) berdasarkan daftar skenario di bawah.
{doc_block}{focus_req_block}
DAFTAR SKENARIO ({test_type}):
{scenarios_render}

INSTRUKSI:
- Untuk SETIAP skenario di atas, buat {target_per_scenario} atau lebih test case yang detail & siap dieksekusi tester.
- Setiap test case HARUS spesifik ke konteks dokumen (langkah & expected result konkret, bukan generic).
- Pikirkan prekondisi yang relevan, langkah-langkah berurutan, dan expected result yang terverifikasi.
- Ekspand skenario: jangan takut menambah test case tambahan untuk edge case yang Anda temukan saat menulis.

ATURAN KERAS (WAJIB):
- Output HARUS berupa JSON ARRAY MURNI. Tidak boleh markdown, tidak boleh teks di luar array, tidak boleh komentar.
- Format setiap test case PERSIS seperti schema di bawah.

SCHEMA WAJIB (setiap elemen array):
{{
  "tc_id": "{prefix}-001",
  "title": "string - judul deskriptif test case",
  "preconditions": ["string", "..."],
  "steps": ["string", "..."],
  "expected_result": ["string", "..."]
}}

OUTPUT: JSON ARRAY SAJA. Mulai langsung dengan "[" dan akhiri dengan "]".
"""
