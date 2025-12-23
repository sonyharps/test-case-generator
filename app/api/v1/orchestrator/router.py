from fastapi import APIRouter
from app.pipeline.orchestrator_v7 import orchestrate

router = APIRouter(
    prefix="/orchestrator",
    tags=["Orchestrator"]
)

@router.post("/run")
async def run_orch(payload: dict):

    requirement = payload.get("requirement", "")
    model = payload.get("model", "llama3.1:8b")
    #generate_boundary = payload.get("generate_boundary", True)
    #include_risk = payload.get("include_risk_assessment", True)

    result = await orchestrate(
        requirement=requirement,
        model=model,
        #generate_boundary=generate_boundary,
        #include_risk=include_risk,
    )

    return result
