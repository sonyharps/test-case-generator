"""
V8 Full Generate Prompt — single-call end-to-end generation.

Cloud-optimized single-call pipeline. Powerful cloud models (GLM-5-Turbo,
Gemini Flash, Groq Llama-70B) read a full document and emit a complete,
structured test-suite in ONE call.

Output follows ISO/IEC/IEEE 29119-3 & ISTQB test-case design best practices: each test
case is production-grade with priority, concrete test data, measurable
expected results, postconditions, and module tagging.

One call produces: summary + functional[] + negative[] + boundary[] + risk.
"""

from typing import Optional


def _truncate_doc(document_text: str, max_chars: int = 60000) -> str:
    if len(document_text) <= max_chars:
        return document_text
    return document_text[:max_chars] + "\n\n[...dokumen dipotong karena panjang...]"


def build_v8_full_generate_prompt(
    document_text: str,
    requirement: Optional[str] = None,
    generate_boundary: bool = True,
    target_functional: int = 28,
    target_negative: int = 28,
    target_boundary: int = 24,
) -> str:
    """Build the single-call V8 generation prompt.

    Args:
        document_text: The FULL source document text (PRD/user story/etc.).
        requirement: Optional focus requirement (free-text supplement).
        generate_boundary: Whether to demand boundary test cases.
        target_functional: Minimum functional TCs to demand.
        target_negative: Minimum negative TCs to demand.
        target_boundary: Minimum boundary TCs to demand.

    Returns:
        The single-call generation prompt string.
    """
    focus_block = ""
    if requirement and requirement.strip():
        focus_block = f"\nFOKUS REQUIREMENT TAMBAHAN (prioritaskan ini):\n{requirement.strip()}\n"

    boundary_block = ""
    if generate_boundary:
        boundary_block = f'''
  "boundary": [
    // Boundary & edge-case test cases (MIN {target_boundary}). Uji batas atas/bawah,
    // nilai ekstrem, off-by-one, overflow, dan transisi state.
    {_tc_example()}
  ],'''
    else:
        boundary_block = '\n  "boundary": [],  // boundary generation disabled'

    return f"""Anda adalah Principal QA Engineer bersertifikat ISTQB dengan 15+ tahun pengalaman di industri finance/banking.

TUGAS UTAMA:
Baca SECARA MENYELURUH dokumen sumber berikut (PRD / User Story / Spec), pahami setiap fitur, alur, aturan bisnis, validasi, dan edge case. Lalu hasilkan **SUITE TEST CASE PRODUCTION-GRADE** mengikuti standar ISO/IEC/IEEE 29119-3 & ISTQB dalam SATU output JSON.

DOKUMEN SUMBER:
---
{_truncate_doc(document_text)}
---
{focus_block}
PRINSIP QUALITY (WAJIB DIKETAHUI):
1. Setiap test case harus ATOMIC — menguji SATU hal spesifik, bukan beberapa sekaligus.
2. Steps harus ACTIONABLE — setiap step adalah aksi konkret yang bisa dieksekusi tester (klik tombol X, input nilai Y, navigasi ke halaman Z). JANGAN abstrak seperti "lakukan testing".
3. Expected Result harus MEASURABLE & OBSERVABLE — harus bisa diverifikasi secara objektif (UI menampilkan pesan tertentu, status berubah ke nilai A, field dinonaktifkan, HTTP response 400). Hindari kata samar seperti "sistem berjalan baik".
4. Test Data harus KONKRET — sebutkan nilai/nama data spesifik (contoh: "jumlah transfer Rp7.500.000", "user: customer01 dengan saldo Rp2.000.000"). Jangan placeholder generik seperti "data valid".
5. Preconditions harus SPESIFIK & TESTABLE — kondisi awal yang harus benar-benar dicek sebelum test (contoh: "User sudah login sebagai AO Teller", "Database memiliki minimal 5 nasabah dengan status active").
6. Priority: P0 (blocker/critical path), P1 (major feature), P2 (important), P3 (nice-to-have/cosmetic).
7. Module: kelompok fitur yang diuji (contoh: "Login", "Transfer", "Approval", "Reporting").
8. Hindari DUPLIKASI — tiap TC menguji skenario unik, bukan variasi trivial dari TC lain.

INSTRUKSI GENERATION:
1. Identifikasi SEMUA fitur/fungsi yang bisa diuji dari dokumen.
2. Untuk setiap fitur, cakupi: alur normal (functional), kondisi gagal (negative), dan batas ekstrem (boundary).
3. Pikirkan dari sudut pandang: pengguna akhir, admin/operator, integrasi sistem, keamanan, performa, dan data integrity.
4. Sebutkan konteks konkret dari dokumen di setiap TC — bukan template generik.

ATURAN OUTPUT (KERAS):
- SELURUH output HARUS DALAM BAHASA INDONESIA — semua field (title, priority, module, preconditions, test_data, steps, expected_result, postconditions). Istilah teknis boleh English tapi kalimatnya harus Bahasa Indonesia. DILARANG menulis test case dalam Bahasa Inggris.
- Steps ditulis TANPA nomor urut di depan (cukup kalimat aksinya, penomoran otomatis oleh sistem).
- Output HARUS JSON MURNI. TIDAK BOLEH markdown (```), tidak boleh teks di luar JSON, tidak boleh komentar.
- Setiap test case HARUS spesifik ke dokumen sumber.
- tc_id HARUS format: TC-F-###, TC-N-###, TC-B-### (sequential per kategori).

FORMAT WAJIB (JSON object):
{{
  "summary": {{
    "id": "REQ-001",
    "nama": "string - judul fitur/requirement utama dari dokumen",
    "deskripsi": "string - ringkasan singkat apa yang diuji, merujuk isi dokumen",
    "prioritas": "High | Medium | Low",
    "kategori": "string - domain/klasifikasi",
    "fitur_kunci": ["string", "string", "..."]
  }},
  "functional": [
    // Functional/happy-path test cases (MIN {target_functional})
    {_tc_example()}
  ],
  "negative": [
    // Negative/error-handling test cases (MIN {target_negative})
    {_tc_example()}
  ],{boundary_block}
  "risk": {{
    "level": "Low | Medium | High",
    "notes": ["string - catatan risiko utama"]
  }}
}}

OUTPUT JSON SAJA. Mulai langsung dengan "{{" dan akhiri dengan "}}".
"""


def _tc_example() -> str:
    """Return a concrete ISO/IEC/IEEE 29119-3 test-case example object for in-context guidance."""
    return '''{
    "tc_id": "TC-F-001",
    "title": "string deskriptif - satu kalimat jelas tentang apa yang diuji",
    "priority": "P0 | P1 | P2 | P3",
    "module": "string - kelompok fitur yang diuji",
    "preconditions": [
      "kondisi awal yang harus terpenuhi sebelum test (spesifik & testable)"
    ],
    "test_data": [
      "data konkret spesifik yang dipakai (nilai, input, kredensial)"
    ],
    "steps": [
      "aksi konkret pertama (klik/input/navigasi)",
      "aksi konkret kedua",
      "aksi konkret ketiga"
    ],
    "expected_result": [
      "hasil observable step-1 (jumlah item = jumlah steps, per-step sesuai 29119-3)",
      "hasil observable step-2",
      "hasil observable step-3"
    ],
    "postconditions": [
      "kondisi sistem SETELAH test selesai (state change, data change)"
    ]
  }'''
