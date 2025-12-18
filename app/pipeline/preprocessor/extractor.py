# app/pipeline/preprocessor/extractor.py

def extract(text: str) -> list:
    """
    Extract fields/entities sederhana.
    Bisa diperluas untuk NLP real.
    """

    keywords = ["email", "password", "username", "otp", "phone", "token"]
    found = []

    for key in keywords:
        if key in text:
            found.append(key)

    return found
