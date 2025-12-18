from .risk import assess_risk
from .coverage import compute_coverage

def analyze_test_cases(tc):
    risk = assess_risk(tc)
    cov = compute_coverage(tc)
    return {
        "summary": f"{len(tc.functional)} functional, {len(tc.negative)} negative.",
        "risk": risk,
        "coverage": cov,
        "metadata": {"time": "now", "model": "llama3.1:8b"}
    }
