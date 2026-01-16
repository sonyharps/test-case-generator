"""Test Management / Repository Schemas

Pydantic schemas for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum


# =====================================================
# Enums
# =====================================================
class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AutomationStatus(str, Enum):
    AUTOMATED = "automated"
    MANUAL = "manual"
    TO_BE_AUTOMATED = "to_be_automated"
    NONE = "none"


class TestCaseType(str, Enum):
    FUNCTIONAL = "functional"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    UI = "ui"
    API = "api"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    OTHER = "other"


class TestRunStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestResultStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    RETEST = "retest"
    PENDING = "pending"


# =====================================================
# Step Schema
# =====================================================
class TestStep(BaseModel):
    step: int
    action: str
    expected: str


# =====================================================
# Project Schemas
# =====================================================
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectResponse(ProjectBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    suite_count: int = 0
    case_count: int = 0

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int


# =====================================================
# Test Suite Schemas
# =====================================================
class TestSuiteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TestSuiteCreate(TestSuiteBase):
    project_id: int
    parent_id: Optional[int] = None


class TestSuiteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    position: Optional[int] = None


class TestSuiteResponse(TestSuiteBase):
    id: int
    project_id: int
    parent_id: Optional[int] = None
    position: int
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    case_count: int = 0

    class Config:
        from_attributes = True


class TestSuiteTree(TestSuiteResponse):
    """Test suite with nested children and test cases"""
    children: List["TestSuiteTree"] = []
    test_cases: List["RepositoryTestCaseResponse"] = []


class TestSuiteListResponse(BaseModel):
    suites: List[TestSuiteResponse]
    total: int


# =====================================================
# Repository Test Case Schemas
# =====================================================
class RepositoryTestCaseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    tc_type: TestCaseType = TestCaseType.FUNCTIONAL
    priority: Priority = Priority.MEDIUM
    automation_status: AutomationStatus = AutomationStatus.MANUAL
    estimated_minutes: Optional[int] = None
    tags: Optional[List[str]] = []


class RepositoryTestCaseCreate(RepositoryTestCaseBase):
    suite_id: Optional[int] = None  # Optional for orchestrator save flow (will be set by backend)
    external_id: Optional[str] = None
    preconditions: Optional[List[str]] = []
    steps: Optional[List[TestStep]] = []
    expected_result: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class RepositoryTestCaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    tc_type: Optional[TestCaseType] = None
    priority: Optional[Priority] = None
    automation_status: Optional[AutomationStatus] = None
    estimated_minutes: Optional[int] = None
    tags: Optional[List[str]] = None
    preconditions: Optional[List[str]] = None
    steps: Optional[List[TestStep]] = None
    expected_result: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    position: Optional[int] = None
    is_draft: Optional[bool] = None
    change_summary: Optional[str] = Field(None, description="Description of changes made for version history")


class RepositoryTestCaseResponse(RepositoryTestCaseBase):
    id: int
    suite_id: int
    external_id: Optional[str] = None
    preconditions: List[str] = []
    steps: List[TestStep] = []
    expected_result: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    position: int
    version: int
    is_draft: bool
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    source_session_id: Optional[str] = None
    step_count: int = 0

    class Config:
        from_attributes = True


class RepositoryTestCaseListResponse(BaseModel):
    test_cases: List[RepositoryTestCaseResponse]
    total: int
    page: int
    page_size: int


# =====================================================
# Bulk Operations
# =====================================================
class BulkOperation(BaseModel):
    test_case_ids: List[int]


class BulkUpdateRequest(BaseModel):
    test_case_ids: List[int]
    updates: RepositoryTestCaseUpdate


class BulkDeleteResponse(BaseModel):
    deleted_count: int
    deleted_ids: List[int]


class BulkUpdateResponse(BaseModel):
    updated_count: int
    updated_ids: List[int]


# =====================================================
# Import/Export
# =====================================================
class ImportTestCaseRequest(BaseModel):
    suite_id: int
    test_cases: List[RepositoryTestCaseCreate]
    overwrite: bool = False


class ImportResponse(BaseModel):
    imported_count: int
    updated_count: int
    failed_count: int
    errors: List[str] = []


class ExportRequest(BaseModel):
    suite_id: Optional[int] = None
    project_id: Optional[int] = None
    format: Literal["csv", "json"] = "json"


# =====================================================
# From Orchestrator
# =====================================================
class SaveToRepositoryRequest(BaseModel):
    """Save generated test cases to repository"""
    project_id: Optional[int] = None
    project_name: Optional[str] = None  # Create new project if specified
    suite_id: Optional[int] = None
    suite_name: Optional[str] = None  # Create new suite if specified
    test_cases: List[RepositoryTestCaseCreate]
    source_session_id: Optional[str] = None


class SaveToRepositoryResponse(BaseModel):
    project_id: int
    suite_id: int
    created_count: int
    test_case_ids: List[int]


# =====================================================
# Milestone Schemas
# =====================================================
class MilestoneBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class MilestoneCreate(MilestoneBase):
    project_id: int
    due_date: Optional[datetime] = None


class MilestoneUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None


class MilestoneResponse(MilestoneBase):
    id: int
    project_id: int
    due_date: Optional[datetime] = None
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None

    class Config:
        from_attributes = True


class MilestoneListResponse(BaseModel):
    milestones: List[MilestoneResponse]
    total: int


# =====================================================
# Test Run Schemas
# =====================================================
class TestRunBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TestRunCreate(TestRunBase):
    project_id: int
    milestone_id: Optional[int] = None
    include_all: bool = False
    included_case_ids: Optional[List[int]] = None


class TestRunUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TestRunStatus] = None
    milestone_id: Optional[int] = None


class TestRunResponse(TestRunBase):
    id: int
    project_id: int
    milestone_id: Optional[int] = None
    status: TestRunStatus
    include_all: bool
    included_case_ids: Optional[List[int]] = None
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    progress: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class TestRunListResponse(BaseModel):
    test_runs: List[TestRunResponse]
    total: int


# =====================================================
# Test Result Schemas
# =====================================================
class TestResultCreate(BaseModel):
    test_case_id: int
    status: TestResultStatus = TestResultStatus.PENDING
    assigned_to_id: Optional[int] = None
    actual_result: Optional[str] = None
    comments: Optional[str] = None
    defects: Optional[List[str]] = None
    execution_seconds: Optional[int] = None


class EvidenceItem(BaseModel):
    """Evidence item attached to a test result"""
    id: str  # Unique ID for the evidence item
    type: Literal["image", "video"]  # Type of evidence
    url: str  # URL to access the evidence
    thumbnail_url: Optional[str] = None  # Thumbnail for videos
    filename: str  # Original filename
    size_bytes: int  # File size in bytes
    uploaded_at: datetime  # When it was uploaded


class TestResultUpdate(BaseModel):
    status: Optional[TestResultStatus] = None
    assigned_to_id: Optional[int] = None
    actual_result: Optional[str] = None
    comments: Optional[str] = None
    defects: Optional[List[str]] = None
    execution_seconds: Optional[int] = None
    evidence: Optional[List[str]] = None  # List of evidence IDs to attach


class TestResultResponse(BaseModel):
    id: int
    test_run_id: int
    test_case_id: int
    status: TestResultStatus
    assigned_to_id: Optional[int] = None
    actual_result: Optional[str] = None
    comments: Optional[str] = None
    defects: Optional[List[str]] = None
    execution_seconds: Optional[int] = None
    executed_at: Optional[datetime] = None
    executed_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    evidence: Optional[List[EvidenceItem]] = None  # Attached evidence

    # Include test case details for convenience
    test_case: Optional[RepositoryTestCaseResponse] = None

    class Config:
        from_attributes = True


class TestResultListResponse(BaseModel):
    results: List[TestResultResponse]
    total: int


# =====================================================
# Test Run with Results
# =====================================================
class TestRunWithResultsResponse(TestRunResponse):
    """Test run with all test results included"""
    test_results: List[TestResultResponse] = []


# =====================================================
# Bulk Result Update
# =====================================================
class BulkResultUpdate(BaseModel):
    """Update multiple test results at once"""
    result_ids: List[int]
    status: Optional[TestResultStatus] = None
    assigned_to_id: Optional[int] = None


class BulkResultUpdateResponse(BaseModel):
    updated_count: int
    updated_ids: List[int]


# =====================================================
# Test Case Version History
# =====================================================
class TestCaseVersionResponse(BaseModel):
    """A historical version of a test case"""
    id: int
    test_case_id: int
    version: int
    title: str
    description: Optional[str] = None
    tc_type: TestCaseType
    priority: Priority
    automation_status: AutomationStatus
    estimated_minutes: Optional[int] = None
    preconditions: Optional[List[str]] = None
    steps: Optional[List[Step]] = None
    expected_result: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = None
    changed_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestCaseVersionListResponse(BaseModel):
    """List of versions for a test case"""
    versions: List[TestCaseVersionResponse]
    total: int


class RestoreVersionRequest(BaseModel):
    """Request to restore a test case to a previous version"""
    change_summary: Optional[str] = Field(None, description="Optional description of why this version was restored")


# Update forward references
TestSuiteTree.model_rebuild()
