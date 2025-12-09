from fastapi import APIRouter, Response
from app.services.tc_generator_json import generate_tc_json
from app.services.negative_tc_generator_json import generate_negative_tc_json
from app.services.pdf_exporter import export_tc_pdf

router = APIRouter()

@router.post("/pdf")
async def export_pdf(payload: dict):
    requirement = payload.get("requirement", "")
    tc_type = payload.get("type", "functional")
    model = payload.get("model", "llama3.1:8b")

    if tc_type == "functional":
        tcs = generate_tc_json(requirement, model)
    else:
        tcs = generate_negative_tc_json(requirement, model)

    pdf_path = export_tc_pdf(tcs)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    return Response(content=pdf_bytes, media_type="application/pdf")
