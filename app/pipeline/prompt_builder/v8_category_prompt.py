"""
V8 Category-Focused Prompts — one call PER test-case category.

Companion to `v8_full_generate_prompt` for high-volume generation. Instead of
asking one call to produce functional + negative + boundary together (which
caps output at the model's single-response token limit), each category gets
its OWN dedicated call with the FULL token budget, focused instructions, and
category-specific test-design techniques. The three calls run in parallel,
so wall-clock time stays ~the same as a single call while volume triples.

All prompts demand the same ISO/IEC/IEEE 29119-3 & ISTQB 9-field test-case structure
produced by `v8_full_generate_prompt._tc_example()`.
"""

from typing import Optional

from app.pipeline.prompt_builder.v8_full_generate_prompt import (
    _tc_example,
    _truncate_doc,
)

# Category-specific test-design guidance injected into each prompt.
CATEGORY_INSTRUCTIONS = {
    "functional": """FOKUS KATEGORI: FUNCTIONAL / HAPPY-PATH
Teknik desain test yang HARUS diterapkan:
- Equivalence Partitioning: pisahkan input menjadi kelas valid, uji perwakilan tiap kelas.
- User Journey Coverage: ikuti alur end-to-end setiap role (RM, AO, Teller, nasabah) dari dokumen.
- Role-based Testing: uji alur yang sama dari sudut pandang role berbeda (permission-nya beda).
- State Transition Testing: uji transisi status yang valid (Draft → Submitted → Approved, dsb).
- Integration Points: uji interaksi antar modul yang disebut dokumen (core, payment, notifikasi).
Setiap fitur utama dari dokumen WAJIB punya minimal 1 functional TC.""",

    "negative": """FOKUS KATEGORI: NEGATIVE / ERROR-HANDLING
Teknik desain test yang HARUS diterapkan:
- Error Guessing: input invalid, format salah, field kosong, special chars, XSS payload ("<script>alert(1)</script>"), SQL injection ("' OR 1=1--").
- Invalid State Transitions: coba aksi di state yang salah (approve dokumen yang sudah approved, edit data locked).
- Permission/Authorization Failure: role salah mencoba aksi (staff approve yang harusnya kabag, akses data squad lain).
- Network/System Failure: timeout dari downstream, response invalid dari third-party, service down.
- Business Rule Violation: nilai di luar kebijakan (limit harian terlampaui, umur nasabah tidak memenuhi, skor di bawah threshold).
Setiap validasi & aturan bisnis di dokumen WAJIB punya minimal 1 negative TC.""",

    "boundary": """FOKUS KATEGORI: BOUNDARY / EDGE-CASE
Teknik desain test yang HARUS diterapkan:
- Boundary Value Analysis: uji tepat di batas (min, min+1, min-1, max, max+1, max-1) untuk SETIAP field numerik/range di dokumen.
- Off-by-one Errors: pagination (page 0, page terakhir, page melebihi total), jumlah item (0, 1, N, N+1).
- Data Extremes: string terpanjang yang diizinkan, unicode/emoji, angka desimal vs integer, nilai negatif, leading zeros.
- Time-based Boundaries: jam kerja vs luar jam kerja, tanggal cutoff, akhir bulan/tahun, timezone berbeda, Kabisat (29 Feb).
- Capacity Limits: jumlah record maksimum, ukuran upload maksimum, concurrent users sesuai dokumen.
Setiap range/batas/limit yang disebut dokumen WAJIB punya boundary TC di tepi bawah DAN tepi atas.""",
}


def build_v8_category_prompt(
    category: str,
    document_text: str,
    requirement: Optional[str] = None,
    target: int = 60,
) -> str:
    """Build a single-category focused generation prompt.

    Args:
        category: One of "functional" | "negative" | "boundary".
        document_text: The FULL source document text (PRD/user story/etc.).
        requirement: Optional focus requirement (free-text supplement).
        target: Minimum number of test cases to demand.

    Returns:
        Prompt string whose expected output is a JSON array of test cases.
    """
    if category not in CATEGORY_INSTRUCTIONS:
        raise ValueError(f"Unknown category '{category}'. Must be one of {list(CATEGORY_INSTRUCTIONS)}")

    focus_block = ""
    if requirement and requirement.strip():
        focus_block = f"\nFOKUS REQUIREMENT TAMBAHAN (prioritaskan ini):\n{requirement.strip()}\n"

    cat_instruction = CATEGORY_INSTRUCTIONS[category]
    prefix = {"functional": "TC-F", "negative": "TC-N", "boundary": "TC-B"}[category]

    return f"""Anda adalah Principal QA Engineer bersertifikat ISTQB dengan 15+ tahun pengalaman di industri finance/banking.

TUGAS UTAMA:
Baca SECARA MENYELURUH dokumen sumber berikut, pahami setiap fitur, alur, aturan bisnis, validasi, dan batasan numerik. Lalu hasilkan test case **HANYA untuk kategori: {category.upper()}** — bukan kategori lain.

DOKUMEN SUMBER:
---
{_truncate_doc(document_text)}
---
{focus_block}{cat_instruction}

PRINSIP QUALITY (WAJIB — mengikuti ISO/IEC/IEEE 29119-3 Test Case Specification):
1. Setiap test case harus ATOMIC — menguji SATU hal spesifik.
2. Steps harus ACTIONABLE — aksi konkret yang bisa dieksekusi tester (klik tombol X, input nilai Y).
3. Expected Result harus MEASURABLE & OBSERVABLE dan ditulis PER-STEP: jumlah item expected_result HARUS SAMA dengan jumlah steps, dan item ke-i memverifikasi hasil step ke-i (verifikasi bertahap sesuai 29119-3). Hindari "sistem berjalan baik".
4. Test Data harus KONKRET — sebutkan nilai spesifik ("jumlah transfer Rp7.500.000", "skor 970"). Jangan "data valid".
5. Preconditions harus SPESIFIK & TESTABLE — kondisi awal yang bisa dicek sebelum test.
6. Priority: P0 (blocker/critical path), P1 (major), P2 (important), P3 (nice-to-have).
7. Module = TRACEABILITY ke fitur/requirement di dokumen yang diuji (contoh: "Login", "Transfer", "Approval") — satu fitur per TC, agar bisa dilacak cakupan requirementnya.
8. Hindari DUPLIKASI — tiap TC menguji skenario unik.

ATURAN OUTPUT (KERAS):
- SELURUH output HARUS DALAM BAHASA INDONESIA — semua field (title, priority, module, preconditions, test_data, steps, expected_result, postconditions). Istilah teknis boleh English (mis. "quantity", "checkout") tapi kalimatnya harus Bahasa Indonesia. DILARANG menulis test case dalam Bahasa Inggris.
- Steps ditulis TANPA nomor urut di depan (cukup kalimat aksinya, penomoran otomatis oleh sistem).
- Output HARUS JSON MURNI: sebuah ARRAY berisi MINIMAL {target} test case.
- TIDAK BOLEH markdown, teks di luar JSON, atau komentar.
- tc_id format: {prefix}-### sequential mulai 001.

FORMAT WAJIB (JSON array):
[
  {_tc_example()}
]

OUTPUT JSON ARRAY SAJA. Mulai dengan "[" dan akhiri dengan "]".
"""
