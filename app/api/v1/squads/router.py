"""Squad management router (RBAC). Requires at least ``kabag``."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List

from app.db.session import get_db
from app.api.deps.auth import require_role
from app.models.user import User
from app.models.squad import Squad
from app.schemas.user_schema import (
    SquadCreate,
    SquadUpdate,
    SquadResponse,
    SquadListResponse,
    SquadDetailResponse,
    SquadMemberItem,
)
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=SquadListResponse)
async def list_squads(
    current_user: User = Depends(require_role("kabag")),
    db: AsyncSession = Depends(get_db),
):
    """List all squads with member counts."""
    result = await db.execute(
        select(
            Squad,
            func.count(User.id).label("member_count"),
        )
        .outerjoin(User, User.squad_id == Squad.id)
        .group_by(Squad.id)
        .order_by(Squad.id.asc())
    )
    rows = result.all()

    squads = [
        SquadResponse(
            id=sq.id,
            name=sq.name,
            description=sq.description,
            member_count=count,
            created_at=sq.created_at,
        )
        for sq, count in rows
    ]
    return SquadListResponse(squads=squads, total=len(squads))


@router.post("", response_model=SquadResponse, status_code=status.HTTP_201_CREATED)
async def create_squad(
    payload: SquadCreate,
    current_user: User = Depends(require_role("kabag")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new squad."""
    existing = await db.execute(select(Squad).where(Squad.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Squad name already exists")

    squad = Squad(name=payload.name, description=payload.description)
    db.add(squad)
    await db.commit()
    await db.refresh(squad)
    logger.info("Squad created", actor_id=current_user.id, squad_id=squad.id)
    return SquadResponse(
        id=squad.id,
        name=squad.name,
        description=squad.description,
        member_count=0,
        created_at=squad.created_at,
    )


@router.patch("/{squad_id}", response_model=SquadResponse)
async def update_squad(
    squad_id: int,
    payload: SquadUpdate,
    current_user: User = Depends(require_role("kabag")),
    db: AsyncSession = Depends(get_db),
):
    """Rename or update a squad."""
    result = await db.execute(select(Squad).where(Squad.id == squad_id))
    squad = result.scalar_one_or_none()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")

    if payload.name is not None and payload.name != squad.name:
        dup = await db.execute(select(Squad).where(Squad.name == payload.name))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Squad name already exists")
        squad.name = payload.name
    if payload.description is not None:
        squad.description = payload.description

    await db.commit()
    await db.refresh(squad)

    count_result = await db.execute(select(func.count(User.id)).where(User.squad_id == squad.id))
    member_count = count_result.scalar() or 0
    return SquadResponse(
        id=squad.id,
        name=squad.name,
        description=squad.description,
        member_count=member_count,
        created_at=squad.created_at,
    )


@router.delete("/{squad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_squad(
    squad_id: int,
    current_user: User = Depends(require_role("kabag")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a squad. Members get unassigned (squad_id = NULL)."""
    result = await db.execute(select(Squad).where(Squad.id == squad_id))
    squad = result.scalar_one_or_none()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")

    # Unassign members first
    members = await db.execute(select(User).where(User.squad_id == squad_id))
    for m in members.scalars().all():
        m.squad_id = None

    await db.delete(squad)
    await db.commit()
    logger.info("Squad deleted", actor_id=current_user.id, squad_id=squad_id)
    return None


@router.get("/{squad_id}/members", response_model=SquadDetailResponse)
async def get_squad_members(
    squad_id: int,
    current_user: User = Depends(require_role("kabag")),
    db: AsyncSession = Depends(get_db),
):
    """List members of a squad."""
    result = await db.execute(select(Squad).where(Squad.id == squad_id))
    squad = result.scalar_one_or_none()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")

    members_result = await db.execute(select(User).where(User.squad_id == squad_id).order_by(User.id))
    members = [
        SquadMemberItem(
            id=m.id,
            username=m.username,
            email=m.email,
            full_name=m.full_name,
            role=m.role.value if hasattr(m.role, "value") else m.role,
            is_active=m.is_active,
        )
        for m in members_result.scalars().all()
    ]
    return SquadDetailResponse(
        id=squad.id,
        name=squad.name,
        description=squad.description,
        created_at=squad.created_at,
        members=members,
    )
