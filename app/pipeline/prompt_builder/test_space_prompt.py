def build_test_space_prompt(pre):
    req = pre["clean_requirement"]

    return (
        "Anda adalah Senior QA Engineer.\n"
        "Tugas Anda adalah menganalisis REQUIREMENT dan MEMETAKAN RUANG TESTING.\n\n"

        "ATURAN KETAT:\n"
        "1. Output HARUS JSON VALID\n"
        "2. TANPA markdown, TANPA penjelasan\n"
        "3. Pisahkan dengan jelas SUCCESS, FAILURE, dan BOUNDARY\n"
        "4. Boundary HANYA jika ada limit (panjang, nilai, empty)\n"
        "5. Jika tidak ada boundary → gunakan []\n\n"

        "FORMAT WAJIB:\n"
        "{\n"
        '  "success": ["..."],\n'
        '  "failure": ["..."],\n'
        '  "boundary": ["..."]\n'
        "}\n\n"

        "REQUIREMENT:\n"
        f"{req}\n\n"

        "HASILKAN SEKARANG:"
    )
