def build_tc_generator_prompt(
    expanded_plan,
    req,
    domain,
    tc_type,
    focus: str
):
    return f"""
Anda adalah Senior QA Engineer profesional.

TUGAS:
Buat test case dalam bentuk JSON ARRAY.

Jenis test case:
{tc_type}

Fokus pengujian:
{focus}

Requirement:
{req}

Domain:
{domain}

Rencana pengujian:
{expanded_plan}

========================================
ATURAN OUTPUT (WAJIB):
1. Output UTAMA harus berupa JSON ARRAY.
2. Jika Anda menulis penjelasan, JSON HARUS tetap valid & bisa diekstrak.
3. Minimal 5 test case.
4. Setiap test case wajib punya:
   - title
   - steps (minimal 2)
   - expected_result (minimal 1)
========================================

FORMAT WAJIB:
[
  {{
    "tc_id": "",
    "title": "",
    "preconditions": [],
    "steps": [],
    "expected_result": []
  }}
]

CATATAN:
- tc_id boleh dikosongkan (akan diisi sistem)
- Jangan ulangi test case antar jenis
- Fokus sesuai jenis test case

HASILKAN SEKARANG.
"""
