from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class OrchestratorSession(Base, TimestampMixin):
    __tablename__ = "orchestrator_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True, nullable=False)  # UUID

    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="sessions")

    # Request data
    requirement_text = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=False)
    generate_boundary = Column(Boolean, default=True)
    include_risk = Column(Boolean, default=True)

    # Results (stored as JSON)
    summary = Column(JSON)
    coverage_matrix = Column(JSON)
    risk_assessment = Column(JSON)
    session_metadata = Column(JSON)

    # Performance tracking
    execution_time_ms = Column(Integer)

    # Relationships
    test_cases = relationship("TestCaseRecord", back_populates="session", cascade="all, delete-orphan")
