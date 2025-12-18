def build_negative_prompt(pre):
    req = pre["clean_requirement"]
    domain = pre["domain"]

    return (
        "Anda adalah Senior QA Engineer.\n"
        "Buat MINIMAL 3 Negative Test Case dalam JSON VALID.\n\n"
        "ATURAN WAJIB:\n"
        "- Hanya output JSON array.\n"
        "- Tidak ada teks di luar JSON.\n"
        "- Fokus pada input invalid, kesalahan user, dan error handling.\n\n"
        f"Requirement: \"{req}\"\n"
        f"Domain: \"{domain}\"\n\n"
        "FORMAT:\n"
        "[\n"
        "  {\n"
        "    \"tc_id\": \"TC-N-001\",\n"
        "    \"title\": \"\",\n"
        "    \"preconditions\": [],\n"
        "    \"steps\": [],\n"
        "    \"expected_result\": []\n"
        "  }\n"
        "]\n"
        "Hasilkan hanya JSON array minimal 3 testcase."
    )
