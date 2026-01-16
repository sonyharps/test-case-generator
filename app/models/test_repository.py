"""Test Management / Repository Models

Models for managing test cases in a repository structure similar to TestRail.
Hierarchy: Project -> TestSuite -> RepositoryTestCase

Test Runs: TestRun -> TestResult (execution tracking)
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, Enum, Boolean, DateTime
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from .base import Base, TimestampMixin


class Priority(str, enum.Enum):
    """Test case priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AutomationStatus(str, enum.Enum):
    """Automation status of test cases"""
    AUTOMATED = "automated"
    MANUAL = "manual"
    TO_BE_AUTOMATED = "to_be_automated"
    NONE = "none"


class RepositoryTestCaseType(str, enum.Enum):
    """Extended test case types for repository"""
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


class TestRunStatus(str, enum.Enum):
    """Status of a test run"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestResultStatus(str, enum.Enum):
    """Status of a test execution result"""
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    RETEST = "retest"
    PENDING = "pending"

    @staticmethod
    def to_lower(status: str) -> str:
        """Convert uppercase status string to lowercase for database"""
        return status.lower() if status and status.upper() in [s.name for s in TestResultStatus] else status

    @classmethod
    def from_str(cls, value: str) -> "TestResultStatus":
        """Get enum from string (case-insensitive)"""
        for status in cls:
            if status.value == value.lower():
                return status
        raise ValueError(f"No matching TestResultStatus for: {value}")


class Project(Base, TimestampMixin):
    """Project represents a testing project/product"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # User who created the project
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")

    # Relationships
    suites = relationship(
        "TestSuite",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="TestSuite.position"
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class TestSuite(Base, TimestampMixin):
    """TestSuite is a container/folder for test cases (can be nested)"""
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, default=0, nullable=False)

    # Hierarchy: suite can belong to a project and optionally a parent suite
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    project = relationship("Project", back_populates="suites")

    parent_id = Column(Integer, ForeignKey("test_suites.id"), nullable=True, index=True)
    parent = relationship("TestSuite", remote_side=[id], backref="children")

    # User who created the suite
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")

    # Relationships
    test_cases = relationship(
        "RepositoryTestCase",
        back_populates="suite",
        cascade="all, delete-orphan",
        order_by="RepositoryTestCase.position"
    )

    def __repr__(self):
        return f"<TestSuite(id={self.id}, name='{self.name}', project_id={self.project_id})>"

    @property
    def case_count(self):
        """Get total count of test cases in this suite (including nested)"""
        direct_count = len(self.test_cases)
        nested_count = sum(child.case_count for child in self.children) if self.children else 0
        return direct_count + nested_count


class RepositoryTestCase(Base, TimestampMixin):
    """RepositoryTestCase represents a reusable test case in the repository"""
    __tablename__ = "repository_test_cases"

    id = Column(Integer, primary_key=True, index=True)

    # External ID (like TC-001, REPO-001)
    external_id = Column(String(50), nullable=True, index=True)

    # Belongs to a suite
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False, index=True)
    suite = relationship("TestSuite", back_populates="test_cases")

    # Basic info
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Classification
    tc_type = Column(
        Enum(RepositoryTestCaseType, values_callable=lambda obj: [e.value for e in obj]),
        default=RepositoryTestCaseType.FUNCTIONAL,
        nullable=False
    )
    priority = Column(
        Enum(Priority, values_callable=lambda obj: [e.value for e in obj]),
        default=Priority.MEDIUM,
        nullable=False
    )
    automation_status = Column(
        Enum(AutomationStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=AutomationStatus.MANUAL,
        nullable=False
    )

    # Estimation
    estimated_minutes = Column(Integer, nullable=True)

    # Test content
    preconditions = Column(JSON, nullable=True)  # List of strings
    steps = Column(JSON, nullable=True)  # List of dicts: [{step: 1, action: "...", expected: "..."}]
    expected_result = Column(Text, nullable=True)

    # Additional data
    tags = Column(JSON, nullable=True)  # List of strings
    custom_fields = Column(JSON, nullable=True)  # Flexible field storage

    # Position for ordering
    position = Column(Integer, default=0, nullable=False)

    # User tracking
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")

    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = relationship("User", foreign_keys=[updated_by_id], lazy="joined")

    # Version tracking
    version = Column(Integer, default=1, nullable=False)
    is_draft = Column(Boolean, default=False, nullable=False)

    # Source tracking (if generated from orchestrator)
    source_session_id = Column(String(36), nullable=True)  # Orchestrator session ID

    def __repr__(self):
        return f"<RepositoryTestCase(id={self.id}, title='{self.title}', type={self.tc_type})>"

    @property
    def step_count(self):
        """Get number of steps"""
        return len(self.steps) if self.steps else 0


class TestRun(Base, TimestampMixin):
    """
    TestRun represents a test execution session.

    A test run contains test results for selected test cases from a project.
    Users can execute tests and record results (passed, failed, blocked, etc.)
    """
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Status tracking
    status = Column(
        Enum(TestRunStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=TestRunStatus.PLANNED,
        nullable=False,
        index=True
    )

    # Relationships
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    project = relationship("Project")

    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True, index=True)
    milestone = relationship("Milestone")

    # User tracking
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")

    completed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    completed_by = relationship("User", foreign_keys=[completed_by_id], lazy="joined")

    # Execution tracking
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Included test case IDs (for quick filtering)
    # When creating a run, user selects specific test cases to include
    include_all = Column(Boolean, default=False, nullable=False)
    included_case_ids = Column(JSON, nullable=True)  # List of repository test case IDs

    # Relationships
    test_results = relationship(
        "TestResult",
        back_populates="test_run",
        cascade="all, delete-orphan",
        order_by="TestResult.id"
    )

    def __repr__(self):
        return f"<TestRun(id={self.id}, name='{self.name}', status={self.status})>"

    @property
    def progress(self):
        """Get progress statistics"""
        total = len(self.test_results)
        if total == 0:
            return {"total": 0, "passed": 0, "failed": 0, "blocked": 0, "skipped": 0, "pending": 0, "pass_rate": 0}

        passed = sum(1 for r in self.test_results if r.status == TestResultStatus.PASSED)
        failed = sum(1 for r in self.test_results if r.status == TestResultStatus.FAILED)
        blocked = sum(1 for r in self.test_results if r.status == TestResultStatus.BLOCKED)
        skipped = sum(1 for r in self.test_results if r.status == TestResultStatus.SKIPPED)
        pending = sum(1 for r in self.test_results if r.status == TestResultStatus.PENDING)
        retest = sum(1 for r in self.test_results if r.status == TestResultStatus.RETEST)

        executed = passed + failed + blocked + retest
        pass_rate = (passed / total * 100) if total > 0 else 0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "blocked": blocked,
            "skipped": skipped,
            "pending": pending + retest,
            "pass_rate": round(pass_rate, 1)
        }


class TestResult(Base, TimestampMixin):
    """
    TestResult represents the execution of a single test case within a test run.
    """
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False, index=True)
    test_run = relationship("TestRun", back_populates="test_results")

    test_case_id = Column(Integer, ForeignKey("repository_test_cases.id"), nullable=False, index=True)
    test_case = relationship("RepositoryTestCase")

    # Execution result
    status = Column(
        Enum(TestResultStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=TestResultStatus.PENDING,
        nullable=False,
        index=True
    )

    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], lazy="joined")

    # Execution details
    actual_result = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)

    # Defect tracking
    defects = Column(JSON, nullable=True)  # List of defect URLs/IDs

    # Execution time
    execution_seconds = Column(Integer, nullable=True)

    # Evidence attachments (images, videos)
    evidence = Column(JSON, nullable=True)  # List of evidence objects with metadata

    # When was this result recorded
    executed_at = Column(DateTime(timezone=True), nullable=True)
    executed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    executed_by = relationship("User", foreign_keys=[executed_by_id], lazy="joined")

    def __repr__(self):
        return f"<TestResult(id={self.id}, status={self.status}, test_case_id={self.test_case_id})>"


class Milestone(Base, TimestampMixin):
    """
    Milestone represents a project milestone (release, sprint, etc.)
    for tracking test execution progress.
    """
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    project = relationship("Project")

    due_date = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False, index=True)

    # User tracking
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")

    # Relationships
    test_runs = relationship("TestRun", back_populates="milestone")

    def __repr__(self):
        return f"<Milestone(id={self.id}, name='{self.name}', completed={self.is_completed})>"


class TestCaseVersion(Base, TimestampMixin):
    """
    TestCaseVersion stores historical versions of test cases.
    When a test case is updated, a new version record is created.
    """
    __tablename__ = "test_case_versions"

    id = Column(Integer, primary_key=True, index=True)

    # Reference to the current test case
    test_case_id = Column(Integer, ForeignKey("repository_test_cases.id"), nullable=False, index=True)
    test_case = relationship("RepositoryTestCase", foreign_keys=[test_case_id])

    # Version number
    version = Column(Integer, nullable=False)

    # Snapshot of the test case data at this version
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    tc_type = Column(
        Enum(RepositoryTestCaseType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    priority = Column(
        Enum(Priority, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    automation_status = Column(
        Enum(AutomationStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    estimated_minutes = Column(Integer, nullable=True)
    preconditions = Column(JSON, nullable=True)
    steps = Column(JSON, nullable=True)
    expected_result = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    custom_fields = Column(JSON, nullable=True)

    # Change tracking
    change_summary = Column(Text, nullable=True)  # Brief description of changes
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    changed_by = relationship("User", foreign_keys=[changed_by_id], lazy="joined")

    # Soft delete support
    is_deleted = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<TestCaseVersion(id={self.id}, test_case_id={self.test_case_id}, version={self.version})>"
