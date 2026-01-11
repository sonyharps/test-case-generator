from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
import enum
from .base import Base, TimestampMixin

class TestCaseType(str, enum.Enum):
    FUNCTIONAL = "functional"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"

class TestCaseStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"

class TestCaseRecord(Base, TimestampMixin):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    tc_id = Column(String(50), index=True, nullable=False)  # TC-F-001, TC-N-002, etc.

    # Session relationship
    session_id = Column(Integer, ForeignKey("orchestrator_sessions.id"), nullable=False)
    session = relationship("OrchestratorSession", back_populates="test_cases")

    # Test case data
    tc_type = Column(Enum(TestCaseType), nullable=False)
    title = Column(String(500), nullable=False)
    preconditions = Column(JSON)  # List[str]
    steps = Column(JSON)  # List[str]
    expected_result = Column(JSON)  # List[str]

    # Phase 2: Approval workflow
    status = Column(String(20), default="draft", nullable=False, index=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Phase 2: Edit tracking
    edited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    edit_count = Column(Integer, default=0, nullable=False)
    original_content = Column(JSON, nullable=True)  # Store original AI-generated content

    # Relationships
    approver = relationship("User", foreign_keys=[approved_by], lazy="joined")
    editor = relationship("User", foreign_keys=[edited_by], lazy="joined")
    comments = relationship("TestCaseComment", back_populates="test_case", cascade="all, delete-orphan")
