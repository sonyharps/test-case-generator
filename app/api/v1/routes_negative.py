from fastapi import APIRouter
from app.services.negative_tc_generator import generate_negative_tc
from app.services.negative_tc_generator_json import generate_negative_tc_json

router = APIRouter()

@router.post("/")
async def generate_negative_testcase(payload: dict):
    requirement = payload.get("requirement", "")
    model = payload.get("model", "llama3.1:8b")

    result = generate_negative_tc(requirement=requirement, model=model)

    return {
        "model_used": model,
        "requirement": requirement,
        "generated_negative_tc": result
    }

@router.post("/json")
async def generate_negative_testcase_json(payload: dict):
    requirement = payload.get("requirement", "")
    model = payload.get("model", "llama3.1:8b")
    result = generate_negative_tc_json(requirement=requirement, model=model)
    return {
        "format": "json",
        "model_used": model,
        "requirement": requirement,
        "generated_negative_tc": result
    }