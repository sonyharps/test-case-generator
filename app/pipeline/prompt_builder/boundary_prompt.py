def build_boundary_prompt(boundary_space: list):
    if not boundary_space:
        return "[]"

    joined = "\n".join(f"- {b}" for b in boundary_space)

    return (
        "Anda adalah Senior QA Engineer.\n"
        "Buat Boundary Test Case.\n\n"
        "ATURAN KRITIS:\n"
        "- HANYA dari daftar boundary\n"
        "- Fokus MIN, MAX, EMPTY, OVERFLOW\n"
        "- DILARANG skenario umum\n\n"

        "BOUNDARY SCENARIOS:\n"
        f"{joined}\n\n"

        "OUTPUT: JSON ARRAY VALID SAJA."
    )
