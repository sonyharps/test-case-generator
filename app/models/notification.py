from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Notification(Base, TimestampMixin):
    """
    User notifications for events like:
    - Test case generation completed
    - Comment added to test case
    - Approval requested
    - Test case edited
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Notification details
    notification_type = Column(String(50), nullable=False)  # 'generation_complete', 'comment_added', 'approval_requested'
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Related entities
    related_session_id = Column(String(36), nullable=True)
    related_test_case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="SET NULL"), nullable=True)

    # Status tracking
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    is_emailed = Column(Boolean, default=False, nullable=False)
    emailed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", lazy="joined")
    test_case = relationship("TestCaseRecord", lazy="joined")
