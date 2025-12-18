QA_GLOBAL_RULES = """
### ATURAN GLOBAL (WAJIB):

1. Jawaban HARUS Bahasa Indonesia formal.
2. Tidak boleh ada teks di luar JSON untuk output test case.
3. JSON harus VALID (harus bisa di-parse Python).
4. steps dan expected_result wajib berupa array of string.
5. tc_id harus format TC-001, TC-002, ...
6. Gunakan konteks domain jika tersedia (e.g., banking, ecommerce, healthcare).
7. Jangan menyisipkan catatan, penjelasan, analisis—kecuali diminta.
"""
