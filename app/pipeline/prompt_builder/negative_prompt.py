def build_negative_prompt(failure_space):
    return f"""
Anda adalah Senior QA Engineer.

Berdasarkan skenario NEGATIVE berikut:
{failure_space}

Buat TEST CASE NEGATIVE.

WAJIB output JSON ARRAY.
Gunakan format SAMA seperti functional.

FOKUS:
- input tidak valid
- data kosong
- kredensial salah
- kondisi gagal

HANYA JSON.
"""
