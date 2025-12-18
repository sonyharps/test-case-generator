# app/pipeline/preprocessor/classifier.py

def classify(text: str) -> str:
    """
    Domain classification sangat sederhana,
    nanti bisa pakai model kecil khusus classifier.
    """

    if any(x in text for x in ["login", "auth", "token"]):
        return "authentication"

    if "payment" in text:
        return "payment"

    if "register" in text:
        return "registration"

    return "general"
