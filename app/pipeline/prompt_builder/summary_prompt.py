def build_summary_prompt(pre):
    req = pre["clean_requirement"]

    return (
        "Anda adalah sistem ekstraksi requirement profesional.\n"
        "\n"
        "=== ATURAN KELUARAN ===\n"
        "1. Hanya keluarkan JSON VALID.\n"
        "2. Tidak boleh ada markdown.\n"
        "3. Tidak boleh ada ``` atau teks tambahan.\n"
        "4. Output HARUS mulai dengan '{' dan berakhir dengan '}'.\n"
        "5. Semua field WAJIB terisi (tidak boleh kosong).\n"
        "\n"
        "=== KETENTUAN FIELD ===\n"
        "- id: selalu gunakan format REQ-001.\n"
        "- nama: ringkas dan menggambarkan tujuan utama requirement.\n"
        "- deskripsi: ringkasan 1–2 kalimat dari requirement.\n"
        "- prioritas: tentukan otomatis salah satu dari: High, Medium, Low.\n"
        "- kategori: tentukan kategori fungsional seperti:\n"
        "  Authentication, Authorization, User Management, CRUD, Security,\n"
        "  Performance, Payment, Notification, UI/UX, Logging, Validation.\n"
        "\n"
        "=== FORMAT FINAL ===\n"
        "{\n"
        '  "kriteria": [\n'
        "    {\n"
        '      "id": "REQ-001",\n'
        '      "nama": "…",\n'
        '      "deskripsi": "…",\n'
        '      "prioritas": "High/Medium/Low",\n'
        '      "kategori": "…" \n'
        "    }\n"
        "  ]\n"
        "}\n"
        "\n"
        f"Requirement yang harus diringkas:\n{req}\n\n"
        "=== HASILKAN SEKARANG: JSON LENGKAP & VALID ==="
    )
