from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Requirement(Base, TimestampMixin):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)

    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="requirements")

    # Requirement data
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    tags = Column(String(500))  # Comma-separated

    # Library metadata
    is_template = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
