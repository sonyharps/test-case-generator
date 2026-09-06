"""Project management router.

GET  /v1/projects        — any authenticated user (needed for filters/labels)
POST/PATCH/DELETE        — kabag and above

A project is a work grouping; the squad→project mapping lives on the squad
(PATCH /v1/squads/{id} with project_id).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.session import get_db
from app.api.deps.auth import require_role, get_current_active_user
from app.models.user import User
from app.models.project import Project
from app.models.squad import Squad
from app.models.session import OrchestratorSession
from app.models.test_case import TestCaseRecord
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    code: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    code: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    session_count: int = 0
    test_case_count: int = 0
    squads: list = []  # [{"id": int, "name": str}]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List projects with per-project session/TC counts and squad mapping."""
    result = await db.execute(
        select(
            Project,
            func.count(func.distinct(OrchestratorSession.id)).label("session_count"),
            func.count(TestCaseRecord.id).label("tc_count"),
        )
        .outerjoin(OrchestratorSession, OrchestratorSession.project_id == Project.id)
        .outerjoin(TestCaseRecord, TestCaseRecord.session_id == OrchestratorSession.id)
        .group_by(Project.id)
        .order_by(Project.name.asc())
    )
    rows = result.all()

    squads_result = await db.execute(select(Squad).where(Squad.project_id.isnot(None)))
    squads_by_project: dict = {}
    for sq in squads_result.scalars().all():
        squads_by_project.setdefault(sq.project_id, []).append(
            {"id": sq.id, "name": sq.name}
        )

    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            code=p.code,
            description=p.description,
            is_active=p.is_active,
            session_count=sess or 0,
            test_case_count=tc or 0,
            squads=squads_by_project.get(p.id, []),
            created_at=p.created_at,
        )
        for p, sess, tc in rows
    ]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(require_role("kabag")),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Project).where(Project.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Project name already exists")
    if payload.code:
        dup = await db.execute(select(Project).where(Project.code == payload.code))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Project code already exists")

    project = Project(name=payload.name, code=payload.code, description=payload.description)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    logger.info("Project created", actor_id=current_user.id, project_id=project.id)
    return ProjectResponse(
        id=project.id, name=project.name, code=project.code,
        description=project.description, is_active=project.is_active,
        session_count=0, test_case_count=0, squads=[], created_at=project.created_at,
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    current_user: User = Depends(require_role("kabag")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.name is not None and payload.name != project.name:
        dup = await db.execute(select(Project).where(Project.name == payload.name))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Project name already exists")
        project.name = payload.name
    if payload.code is not None:
        project.code = payload.code
    if payload.description is not None:
        project.description = payload.description
    if payload.is_active is not None:
        project.is_active = payload.is_active

    await db.commit()
    await db.refresh(project)
    return ProjectResponse(
        id=project.id, name=project.name, code=project.code,
        description=project.description, is_active=project.is_active,
        session_count=0, test_case_count=0, squads=[], created_at=project.created_at,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(require_role("kabag")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Unmap squads first; keep historical session/document stamps as-is
    squads = await db.execute(select(Squad).where(Squad.project_id == project_id))
    for sq in squads.scalars().all():
        sq.project_id = None

    await db.delete(project)
    await db.commit()
    logger.info("Project deleted", actor_id=current_user.id, project_id=project_id)
    return None
