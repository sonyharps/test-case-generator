# app/pipeline/prompt_builder/reasoning_prompt.py

def build_reasoning_prompt(req: str):
    return (
        "Anda adalah AI System Analyst senior.\n"
        "Analisis requirement berikut secara mendalam.\n\n"

        "KELUARKAN DALAM JSON VALID TANPA MARKDOWN:\n"
        "{\n"
        '  "goals": [],\n'
        '  "primary_actions": [],\n'
        '  "user_intent": [],\n'
        '  "constraints": [],\n'
        '  "business_rules": [],\n'
        '  "risks": [],\n'
        '  "edge_cases": [],\n'
        '  "missing_clarifications": []\n'
        "}\n\n"

        "Requirement:\n"
        f"{req}\n\n"

        "HASILKAN HANYA JSON VALID. TANPA MARKDOWN, TANPA BACKTICK."
    )
