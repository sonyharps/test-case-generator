def build_boundary_prompt(pre):
    req = pre["clean_requirement"]
    domain = pre["domain"]

    return (
        "Anda adalah Senior QA Engineer.\n"
        "Buat MINIMAL 2 Boundary Test Case dalam JSON VALID.\n\n"
        "ATURAN:\n"
        "- Output hanya JSON array []\n"
        "- Boundary = nilai maksimum, minimum, empty, null, dan edge case lain yang relevan.\n"
        "- Tidak boleh ada penjelasan di luar JSON.\n\n"
        f"Requirement: \"{req}\"\n"
        f"Domain: \"{domain}\"\n\n"
        "FORMAT:\n"
        "[\n"
        "  {\n"
        "    \"tc_id\": \"TC-B-001\",\n"
        "    \"title\": \"\",\n"
        "    \"boundary_type\": \"\",\n"
        "    \"preconditions\": [],\n"
        "    \"steps\": [],\n"
        "    \"expected_result\": []\n"
        "  }\n"
        "]\n"
        "Hasilkan hanya JSON array minimal 2 test case."
    )
