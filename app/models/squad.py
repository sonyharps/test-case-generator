import enum
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    """User roles ordered by privilege level (see ``level``).

    Storage: native PostgreSQL enum type ``userrole`` with lowercase
    labels (``admin``, ``kabag``, ``qa_lead``, ``qa_staff``).
    """

    ADMIN = "admin"
    KABAG = "kabag"
    QA_LEAD = "qa_lead"
    QA_STAFF = "qa_staff"

    @property
    def level(self) -> int:
        """Numeric privilege level — higher means more powerful.

        Used by the RBAC layer (``require_role``) so that requiring a
        role also implicitly grants access to every more powerful role.
        """
        return ROLE_LEVELS[self.value]


# Privilege ordering (low -> high). Keep in sync with the frontend
# ``ROLE_LEVELS`` map in ``web/src/lib/roles.ts``.
ROLE_LEVELS = {
    "qa_staff": 10,
    "qa_lead": 20,
    "kabag": 40,
    "admin": 80,
}


class Squad(Base, TimestampMixin):
    """A QA squad / team. Members share data visibility under a qa_lead."""

    __tablename__ = "squads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, server_default="true")

    # Active project for this squad — a QA's project follows their squad
    project_id = Column(Integer, ForeignKey("projects.id", use_alter=True), nullable=True, index=True)
    project = relationship("Project", back_populates="squads", foreign_keys=[project_id])

    # Relationships
    members = relationship(
        "User",
        back_populates="squad",
        primaryjoin="Squad.id == User.squad_id",
    )
