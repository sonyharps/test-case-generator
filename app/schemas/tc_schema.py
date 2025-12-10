# app/schemas/tc_schema.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class TestCase(BaseModel):
    tc_id: str
    title: str
    preconditions: List[str]
    steps: List[str]
    expected_result: List[str]

class RiskAssessment(BaseModel):
    level: str  # e.g. low/medium/high
    notes: List[str]

class OrchestratorResult(BaseModel):
    functional: List[TestCase]
    negative: List[TestCase]
    boundary: List[TestCase]
    summary: str
    risk: RiskAssessment
    coverage_matrix: Dict[str, Any]

class OrchestratorRequest(BaseModel):
    requirement: str
    model: str = "llama3.1:8b"
    generate_boundary: bool = True
    include_risk_assessment: bool = True