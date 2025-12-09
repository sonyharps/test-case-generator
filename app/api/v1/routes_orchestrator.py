# app/api/v1/routes_orchestrator.py
from fastapi import APIRouter
from app.services.orchestrator import orchestrate

router = APIRouter()

@router.post("/")
async def run_orchestrator(payload: dict):
    requirement = payload.get("requirement", "")
    model = payload.get("model", "llama3.1:8b")
    generate_boundary = payload.get("generate_boundary", True)
    include_risk = payload.get("include_risk_assessment", True)

    result = orchestrate(requirement=requirement,
                         model=model,
                         generate_boundary=generate_boundary,
                         include_risk=include_risk)
    return result
