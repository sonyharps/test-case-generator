from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from app.db.session import get_db
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from app.models.requirement import Requirement
from app.schemas.requirement_schema import (
    RequirementCreate,
    RequirementUpdate,
    RequirementResponse,
    RequirementListResponse
)
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    requirement_data: RequirementCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new requirement in the library
    """
    logger.info("Creating requirement", user_id=current_user.id, title=requirement_data.title)

    requirement = Requirement(
        user_id=current_user.id,
        title=requirement_data.title,
        description=requirement_data.description,
        tags=requirement_data.tags,
        is_template=requirement_data.is_template,
        usage_count=0
    )

    db.add(requirement)
    await db.commit()
    await db.refresh(requirement)

    logger.info("Requirement created", user_id=current_user.id, requirement_id=requirement.id)

    return requirement


@router.get("", response_model=RequirementListResponse)
async def list_requirements(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search in title, description, or tags"),
    is_template: Optional[bool] = Query(None, description="Filter by template status"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)")
):
    """
    List user's requirements with optional filters
    """
    logger.info("Listing requirements", user_id=current_user.id, skip=skip, limit=limit)

    # Build query
    query = select(Requirement).where(Requirement.user_id == current_user.id)

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Requirement.title.ilike(search_pattern),
                Requirement.description.ilike(search_pattern),
                Requirement.tags.ilike(search_pattern)
            )
        )

    if is_template is not None:
        query = query.where(Requirement.is_template == is_template)

    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag in tag_list:
            query = query.where(Requirement.tags.ilike(f"%{tag}%"))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(Requirement.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    requirements = result.scalars().all()

    logger.info("Requirements listed", user_id=current_user.id, count=len(requirements), total=total)

    return RequirementListResponse(
        requirements=requirements,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(
    requirement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific requirement by ID
    """
    result = await db.execute(
        select(Requirement).where(
            Requirement.id == requirement_id,
            Requirement.user_id == current_user.id
        )
    )
    requirement = result.scalar_one_or_none()

    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    return requirement


@router.put("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: int,
    requirement_data: RequirementUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a requirement
    """
    result = await db.execute(
        select(Requirement).where(
            Requirement.id == requirement_id,
            Requirement.user_id == current_user.id
        )
    )
    requirement = result.scalar_one_or_none()

    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # Update fields
    update_data = requirement_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(requirement, field, value)

    await db.commit()
    await db.refresh(requirement)

    logger.info("Requirement updated", user_id=current_user.id, requirement_id=requirement.id)

    return requirement


@router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(
    requirement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a requirement
    """
    result = await db.execute(
        select(Requirement).where(
            Requirement.id == requirement_id,
            Requirement.user_id == current_user.id
        )
    )
    requirement = result.scalar_one_or_none()

    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    await db.delete(requirement)
    await db.commit()

    logger.info("Requirement deleted", user_id=current_user.id, requirement_id=requirement_id)

    return None


@router.post("/{requirement_id}/use", status_code=status.HTTP_200_OK)
async def use_requirement(
    requirement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Increment usage count when requirement is used
    Returns the requirement description for use in orchestrator
    """
    result = await db.execute(
        select(Requirement).where(
            Requirement.id == requirement_id,
            Requirement.user_id == current_user.id
        )
    )
    requirement = result.scalar_one_or_none()

    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # Increment usage count
    requirement.usage_count += 1
    await db.commit()
    await db.refresh(requirement)

    logger.info("Requirement used", user_id=current_user.id, requirement_id=requirement_id, usage_count=requirement.usage_count)

    return {
        "id": requirement.id,
        "title": requirement.title,
        "description": requirement.description,
        "usage_count": requirement.usage_count
    }
