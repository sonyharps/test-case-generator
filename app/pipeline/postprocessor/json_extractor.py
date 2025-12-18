import json
import re

def extract_first_json(text: str):
    """
    Ambil JSON PERTAMA dari string yang mungkin berisi noise,
    markdown, text biasa, dsb.

    Return:
        dict / list → jika JSON valid
        [] → fallback
    """

    if not text:
        return []

    # Cari blok JSON pakai regex { ... } atau [ ... ]
    pattern = r'(\{.*\}|\[.*\])'
    matches = re.findall(pattern, text, re.DOTALL)

    if not matches:
        return []

    for chunk in matches:
        try:
            return json.loads(chunk)
        except:
            continue

    return []
