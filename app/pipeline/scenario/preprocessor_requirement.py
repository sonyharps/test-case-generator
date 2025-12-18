# app/pipeline/scenario/preprocessor_requirement.py

def preprocess_requirement(req: str) -> str:
    if not req:
        return ""

    text = req.strip()

    # contoh normalisasi
    text = text.replace("login", "user authentication")
    text = text.replace("pwd", "password")

    if not text[0].isupper():
        text = text.capitalize()

    if not text.endswith("."):
        text += "."

    return text
