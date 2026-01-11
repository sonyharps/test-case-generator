from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class TestCaseComment(Base, TimestampMixin):
    """
    Comments on test cases for team collaboration

    Supports threaded comments via parent_comment_id
    """
    __tablename__ = "test_case_comments"

    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    comment_text = Column(Text, nullable=False)

    # Threaded comments support
    parent_comment_id = Column(Integer, ForeignKey("test_case_comments.id", ondelete="CASCADE"), nullable=True)

    # Resolution tracking
    is_resolved = Column(Boolean, default=False, nullable=False)

    # Relationships
    test_case = relationship("TestCaseRecord", back_populates="comments")
    user = relationship("User", lazy="joined")
    parent_comment = relationship("TestCaseComment", remote_side=[id], backref="replies")
