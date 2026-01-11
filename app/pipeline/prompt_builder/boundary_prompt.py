def build_boundary_prompt(boundary_space):
    return f"""
Anda adalah Senior QA Engineer.

Berdasarkan skenario BOUNDARY berikut:
{boundary_space}

Buat TEST CASE BOUNDARY.

WAJIB mencakup:
- minimum
- maksimum
- kosong
- panjang karakter
- limit input

FORMAT JSON ARRAY dengan struktur:
[
  {{
    "title": "Nama test case yang jelas dan deskriptif",
    "preconditions": ["kondisi awal"],
    "steps": ["langkah 1", "langkah 2"],
    "expected_result": ["hasil yang diharapkan"]
  }}
]

PENTING: Setiap test case HARUS memiliki field "title" yang deskriptif.

HANYA JSON.
"""
