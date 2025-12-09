def build_tc_prompt(requirement: str):
    return f"""
Kamu adalah Senior QA Engineer dengan pengalaman lebih dari 15 tahun.

Tugasmu adalah membuat **test case fungsional** berdasarkan requirement berikut.

-----------------------------------------------------
REQUIREMENT:
{requirement}
-----------------------------------------------------

### FORMAT OUTPUT (WAJIB DIIKUTI)

Buat **minimal 5 test case** dengan format berikut:

TC ID: TC-001
Judul: <judul singkat dan jelas>
Prasyarat:
- <daftar prasyarat>
Langkah Pengujian:
1. <langkah 1>
2. <langkah 2>
3. <langkah 3>
Hasil yang Diharapkan:
- <hasil yang terukur dan spesifik>

-----------------------------------------------------

### ATURAN:
- Jangan menulis penjelasan di luar test case.
- Jangan membuat paragraf naratif.
- Hanya tampilkan test case saja.
- TC ID harus berurutan: TC-001, TC-002, TC-003, ...
- Gunakan Bahasa Indonesia formal.
- Hasil yang Diharapkan harus jelas, terukur, tidak ambigu.
- Langkah harus berbentuk aksi, detail, dan bisa dieksekusi.

Sekarang buat test case-nya.
"""
