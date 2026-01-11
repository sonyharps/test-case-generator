from sqlalchemy import Column, String, Integer, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class UsageAnalytics(Base, TimestampMixin):
    __tablename__ = "usage_analytics"

    id = Column(Integer, primary_key=True, index=True)

    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="analytics")

    # Metrics
    endpoint = Column(String(100), nullable=False)  # /v1/orchestrator/run, etc.
    model_used = Column(String(100))
    execution_time_ms = Column(Integer)
    test_cases_generated = Column(Integer, default=0)

    # Timestamp (from TimestampMixin.created_at)
