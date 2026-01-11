def compute_coverage(functional, negative, boundary):
    functional = functional or []
    negative = negative or []
    boundary = boundary or []

    return {
        "functional": len(functional),
        "negative": len(negative),
        "boundary": len(boundary),
        "total": len(functional) + len(negative) + len(boundary)
    }
