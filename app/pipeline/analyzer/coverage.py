def compute_coverage(functional, negative, boundary):
    return {
        "functional_count": len(functional),
        "negative_count": len(negative),
        "boundary_count": len(boundary),
    }
