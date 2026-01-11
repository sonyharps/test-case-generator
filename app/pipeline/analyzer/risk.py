def evaluate_risk(functional, negative, boundary):
    functional = functional or []
    negative = negative or []
    boundary = boundary or []

    risk_level = "Low"
    notes = []

    if len(negative) > len(functional):
        risk_level = "Medium"
        notes.append("Jumlah negative test lebih banyak dari functional")

    if len(boundary) == 0:
        risk_level = "High"
        notes.append("Tidak ada boundary test")

    return {
        "level": risk_level,
        "notes": notes
    }
