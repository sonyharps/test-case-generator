"""Admin user-management router (RBAC).

All endpoints require at least ``kabag``. Only ``admin`` may delete
users or promote another user to ``admin``.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional

from app.db.session import get_db
from app.api.deps.auth import require_role
from app.models.user import User
from app.models.squad import UserRole, ROLE_LEVELS
from app.schemas.user_schema import (
    UserUpdate,
    UserListItem,
    UserListResponse,
    UserResponse,
)
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


def _is_admin(user: User) -> bool:
    role_val = user.role.value if hasattr(user.role, "value") else user.role
    return ROLE_LEVELS.get(role_val, 0) >= ROLE_LEVELS["admin"]


def _to_item(user: User) -> UserListItem:
    return UserListItem(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=user.role.value if hasattr(user.role, "value") else user.role,
        squad_id=user.squad_id,
        squad_name=user.squad.name if user.squad else None,
        created_at=user.created_at,
    )


@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, description="Filter by username/email/full_name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    squad_id: Optional[int] = Query(None, description="Filter by squad"),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(require_role("kabag")),
    db: AsyncSession = Depends(get_db),
):
    """List all users (paginated, filterable). Kabag+ only."""
    query = select(User).options(selectinload(User.squad))
    count_query = select(func.count(User.id))

    if search:
        like = f"%{search}%"
        filt = or_(User.username.ilike(like), User.email.ilike(like), User.full_name.ilike(like))
        query = query.where(filt)
        count_query = count_query.where(filt)
    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)
    if squad_id is not None:
        query = query.where(User.squad_id == squad_id)
        count_query = count_query.where(User.squad_id == squad_id)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.order_by(User.id.asc()).offset(skip).limit(limit))
    users = result.scalars().all()

    return UserListResponse(
        users=[_to_item(u) for u in users], total=total or 0, skip=skip, limit=limit
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_role("kabag")),
    db: AsyncSession = Depends(get_db),
):
    """Get a single user's details. Kabag+ only."""
    result = await db.execute(select(User).options(selectinload(User.squad)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=user.role.value if hasattr(user.role, "value") else user.role,
        squad_id=user.squad_id,
        squad_name=user.squad.name if user.squad else None,
        created_at=user.created_at,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(require_role("kabag")),
    db: AsyncSession = Depends(get_db),
):
    """Update role / is_active / squad_id / full_name / email.

    - Kabag may set roles up to kabag (cannot promote to admin).
    - Only admin may promote to admin or delete.
    """
    result = await db.execute(select(User).options(selectinload(User.squad)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    actor_is_admin = _is_admin(current_user)

    # Role update guard
    if payload.role is not None:
        if payload.role == "admin" and not actor_is_admin:
            raise HTTPException(status_code=403, detail="Only admin may grant the admin role")
        user.role = UserRole(payload.role)

    if payload.is_active is not None:
        user.is_active = payload.is_active
    # squad_id: use a sentinel check — we only skip if the field was omitted
    # entirely (None in JSON), so that an explicit ``null`` can unassign.
    if "squad_id" in payload.dict(exclude_unset=True):
        user.squad_id = payload.squad_id
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        user.email = payload.email

    await db.commit()
    await db.refresh(user)
    # re-load squad relationship after refresh
    await db.refresh(user, attribute_names=["squad"])

    logger.info("User updated", actor_id=current_user.id, target_id=user_id, payload=payload.dict(exclude_none=True))
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=user.role.value if hasattr(user.role, "value") else user.role,
        squad_id=user.squad_id,
        squad_name=user.squad.name if user.squad else None,
        created_at=user.created_at,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user. Admin only. Cannot delete yourself."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    logger.info("User deleted", actor_id=current_user.id, target_id=user_id)
    return None
