def build_test_space_prompt(req: str, domain: str):
    return f"""
Anda adalah Senior QA Architect.

Tugas Anda:
Melakukan TEST SPACE ANALYSIS dari requirement berikut.

Requirement:
{req}

Domain:
{domain}

ATURAN WAJIB:
1. Output HARUS JSON VALID
2. TANPA markdown
3. TANPA teks di luar JSON
4. Setiap array MINIMAL 5 item
5. Setiap item HARUS UNIK dan spesifik

FORMAT WAJIB:
{{
  "functional_space": [
    "..."
  ],
  "negative_space": [
    "..."
  ],
  "boundary_space": [
    "..."
  ]
}}
"""
