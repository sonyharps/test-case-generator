def build_negative_prompt(requirement: str):
    return f"""
Kamu adalah Senior QA Engineer.

Buat **test case NEGATIF** berdasarkan requirement berikut.

-----------------------------------------------------
REQUIREMENT:
{requirement}
-----------------------------------------------------

### FORMAT OUTPUT (WAJIB)

Buat minimal 5 test case negatif dengan format berikut:

TC ID: NEG-001
Judul: <judul singkat>
Prasyarat:
- <prasyarat jika ada>
Langkah Pengujian:
1. <langkah 1>
2. <langkah 2>
Hasil yang Diharapkan:
- <hasil kesalahan yang seharusnya muncul>

-----------------------------------------------------

### ATURAN:
- Fokus pada skenario error, invalid input, edge case.
- Jangan menulis penjelasan tambahan.
- Tidak boleh ada narasi panjang.
- TC ID harus berurutan: NEG-001, NEG-002, ...
- Output harus Bahasa Indonesia resmi.

Sekarang buat test case negatifnya.
"""
