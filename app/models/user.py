from sqlalchemy import Column, String, Boolean, Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from .squad import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)

    # Status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Role — matches the `userrole` PostgreSQL enum. New self-service
    # registrations default to qa_staff (the lowest-privilege role).
    role = Column(
        Enum(UserRole, name="userrole", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.QA_STAFF,
        server_default="qa_staff",
    )

    # Optional squad assignment (FK to squads table)
    squad_id = Column(Integer, ForeignKey("squads.id", use_alter=True), nullable=True, index=True)
    squad = relationship("Squad", back_populates="members", foreign_keys=[squad_id])

    # Relationships
    sessions = relationship("OrchestratorSession", back_populates="user", cascade="all, delete-orphan")
    requirements = relationship("Requirement", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("UsageAnalytics", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("UploadedDocument", back_populates="user", cascade="all, delete-orphan")
