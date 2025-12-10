from fastapi import APIRouter,  Body, HTTPException
from fastapi.responses import FileResponse
from app.services.orchestrator import orchestrate
from app.services.pdf_exporter_v3 import export_orchestrator_pdf_v3
from app.services.pdf_orchestrator_exporter import export_orchestrator_pdf
from app.schemas.tc_schema import OrchestratorRequest

router = APIRouter()

@router.post("/pdf", response_class=FileResponse)
def orchestrate_pdf(payload: dict = Body(...)):
    requirement = payload.get("requirement")
    if not requirement:
        raise HTTPException(status_code=400, detail="requirement is required")

    model = payload.get("model", "llama3.1:8b")
    generate_boundary = payload.get("generate_boundary", True)
    include_risk_assessment = payload.get("include_risk_assessment", True)

    result = orchestrate(
        requirement=requirement,
        model=model,
        generate_boundary=generate_boundary,
        include_risk=include_risk_assessment,
    )

    pdf_path = export_orchestrator_pdf_v3(
        data=result,
        requirement=requirement,
        model_used=model,
        output_path="orchestrator_report.pdf",
    )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="orchestrator_report.pdf",
    )