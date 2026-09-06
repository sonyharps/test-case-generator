from sqlalchemy import Column, String, Text, Integer, Boolean
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    """A work project (e.g. "Mobile Banking QRIS"). Determined per squad:
    ``squads.project_id`` maps each squad to its active project, so a QA's
    project follows automatically from their squad at login."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, index=True, nullable=False)
    code = Column(String(30), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, server_default="true")

    # Relationships
    squads = relationship(
        "Squad",
        back_populates="project",
        primaryjoin="Project.id == Squad.project_id",
    )
