from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class TestCaseResponse(BaseModel):
    """Individual test case response"""
    id: int  # Database ID for editing/approval
    tc_id: str
    title: str
    preconditions: Optional[List[str]] = []
    steps: Optional[List[str]] = []
    expected_result: Optional[List[str]] = []

    # Phase 2: Approval workflow and edit tracking
    status: Optional[str] = "draft"
    edit_count: Optional[int] = 0
    edited_by: Optional[str] = None
    edited_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionSummary(BaseModel):
    """Summary information for a session in list view"""
    id: int
    session_id: str
    requirement_text: str
    model_used: str
    generate_boundary: bool
    include_risk: bool
    execution_time_ms: Optional[int]
    created_at: datetime
    test_case_count: int

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Paginated list of user sessions"""
    sessions: List[SessionSummary]
    total: int
    skip: int
    limit: int


class SessionDetailResponse(BaseModel):
    """Detailed session with all test cases"""
    session_id: str
    requirement_text: str
    model_used: str
    generate_boundary: bool
    include_risk: bool
    execution_time_ms: Optional[int]
    created_at: datetime

    # Test cases grouped by type
    functional: List[TestCaseResponse]
    negative: List[TestCaseResponse]
    boundary: List[TestCaseResponse]

    # Analysis results
    summary: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None
    coverage_matrix: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
