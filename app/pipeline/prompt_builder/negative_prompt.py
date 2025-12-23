def build_negative_prompt(failure_space: list):
    joined = "\n".join(f"- {f}" for f in failure_space)

    return (
        "Anda adalah Senior QA Engineer.\n"
        "Buat MINIMAL 5 Negative Test Case.\n\n"
        "ATURAN KRITIS:\n"
        "- HANYA dari FAILURE\n"
        "- SETIAP test HARUS gagal\n"
        "- DILARANG overlap functional\n\n"

        "FAILURE SCENARIOS:\n"
        f"{joined}\n\n"

        "OUTPUT: JSON ARRAY VALID SAJA."
    )
