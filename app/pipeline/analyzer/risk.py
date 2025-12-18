def evaluate_risk(functional, negative, boundary):
    total = len(functional) + len(negative) + len(boundary)
    if total < 5:
        return {"level": "HIGH", "notes": ["Coverage terlalu sedikit"]}
    if total < 12:
        return {"level": "MEDIUM", "notes": ["Coverage cukup tetapi belum optimal"]}
    return {"level": "LOW", "notes": ["Coverage memadai"]}
