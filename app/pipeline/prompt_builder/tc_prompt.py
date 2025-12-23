def build_functional_prompt(success_space: list):
    joined = "\n".join(f"- {s}" for s in success_space)

    return (
        "Anda adalah Senior QA Engineer.\n"
        "Buat MINIMAL 5 Functional Test Case.\n\n"
        "ATURAN KRITIS:\n"
        "- HANYA dari daftar SUCCESS\n"
        "- DILARANG input invalid, kosong, atau limit\n"
        "- HANYA skenario BERHASIL\n\n"

        "SUCCESS SCENARIOS:\n"
        f"{joined}\n\n"

        "OUTPUT: JSON ARRAY VALID SAJA."
    )
