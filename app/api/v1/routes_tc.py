from fastapi import APIRouter
from app.services.tc_generator import generate_tc
from app.services.tc_generator_json import generate_tc_json


router = APIRouter()

@router.post("/")
async def generate_testcase(payload: dict):
    requirement = payload.get("requirement","")
    model = payload.get("model", "llama3.1:8b")

    result = generate_tc(requirement=requirement, model=model)
    
    return {
        "model_used": model,
        "requirement": requirement,
        "generated_tc": result
    }

@router.post("/json")
async def generate_testcase_json(payload: dict):
    requirement = payload.get("requirement", "")
    model = payload.get("model", "llama3.1:8b")
    result = generate_tc_json(requirement=requirement, model=model)
    return {
        "format": "json",
        "model_used": model,
        "requirement": requirement,
        "generated_test_case": result
    }