def build_functional_prompt(pre):
    req = pre["clean_requirement"]
    domain = pre["domain"]

    return (
        "Anda adalah Senior QA Engineer.\n"
        "Buat MINIMAL 5 functional test case dalam JSON VALID.\n\n"
        "ATURAN WAJIB:\n"
        "- Hanya keluarkan JSON.\n"
        "- JSON harus berupa array [].\n"
        "- Tidak boleh ada markdown, bullet, atau teks di luar JSON.\n"
        "- Semua langkah harus bahasa Indonesia formal.\n"
        "- Gunakan format test case berikut.\n\n"
        f"Requirement: \"{req}\"\n"
        f"Domain: \"{domain}\"\n\n"
        "FORMAT JSON:\n"
        "[\n"
        "  {\n"
        "    \"tc_id\": \"TC-F-001\",\n"
        "    \"title\": \"\",\n"
        "    \"preconditions\": [],\n"
        "    \"steps\": [],\n"
        "    \"expected_result\": []\n"
        "  }\n"
        "]\n"
        "Hasilkan hanya JSON array berisi minimal 5 test case."
    )
