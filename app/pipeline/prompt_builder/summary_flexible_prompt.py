def build_flexible_summary_prompt(pre):
    req = pre["clean_requirement"]

    return (
        "Anda adalah sistem peringkas requirement profesional.\n"
        "Hasilkan ringkasan requirement yang jelas dan terstruktur dalam format JSON VALID.\n"
        "Tidak boleh ada markdown, tidak boleh ada ```.\n"
        "Output harus dimulai dengan '{' dan diakhiri dengan '}'.\n"
        "Tidak boleh ada kalimat atau teks di luar JSON.\n"
        "----------------------------------------\n"
        "FORMAT JSON WAJIB:\n"
        "{\n"
        '  "judul": "",\n'
        '  "deskripsi": "",\n'
        '  "kategori": "",\n'
        '  "prioritas": "Low | Medium | High | Critical",\n'
        '  "fitur_kunci": []\n'
        "}\n\n"
        f"Berikut adalah requirement yang harus diringkas:\n{req}\n\n"
        "HASILKAN JSON valid sekarang."
    )
