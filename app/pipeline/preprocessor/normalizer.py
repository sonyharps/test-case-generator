# app/pipeline/preprocessor/normalizer.py

def normalize(text: str) -> str:
    if not text:
        return ""

    t = text.strip()
    t = t.replace("\n", " ")
    while "  " in t:
        t = t.replace("  ", " ")

    return t.lower()
