from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps.auth import get_current_active_user, get_data_scope
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics_schema import (
    UserStatsResponse,
    TimelineResponse,
    TimelineDataPoint,
    ModelUsageResponse,
    ModelUsageDataPoint,
    TestCaseBreakdownResponse
)
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_statistics(
    current_user: User = Depends(get_current_active_user),
    scope: tuple = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive statistics for the caller's data scope.

    qa_staff → own stats. qa_lead → squad stats. kabag/admin → global stats.
    """
    scope_all, user_ids = scope
    effective_ids = None if scope_all else user_ids
    logger.info("Fetching statistics", user_id=current_user.id, scope_all=scope_all)

    stats = await AnalyticsService.get_user_stats(effective_ids, db)
    return UserStatsResponse(**stats)


@router.get("/timeline", response_model=TimelineResponse)
async def get_sessions_timeline(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    current_user: User = Depends(get_current_active_user),
    scope: tuple = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db)
):
    """Get sessions grouped by date for timeline visualization (scoped)."""
    scope_all, user_ids = scope
    effective_ids = None if scope_all else user_ids

    timeline_data = await AnalyticsService.get_sessions_timeline(effective_ids, db, days)
    timeline_points = [TimelineDataPoint(**point) for point in timeline_data]
    return TimelineResponse(timeline=timeline_points, days=days)


@router.get("/models", response_model=ModelUsageResponse)
async def get_model_usage(
    current_user: User = Depends(get_current_active_user),
    scope: tuple = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db)
):
    """Get breakdown of sessions by model used (scoped)."""
    scope_all, user_ids = scope
    effective_ids = None if scope_all else user_ids

    model_data = await AnalyticsService.get_model_usage(effective_ids, db)
    model_points = [ModelUsageDataPoint(**point) for point in model_data]
    return ModelUsageResponse(model_usage=model_points)


@router.get("/test-cases/breakdown", response_model=TestCaseBreakdownResponse)
async def get_test_case_breakdown(
    current_user: User = Depends(get_current_active_user),
    scope: tuple = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db)
):
    """Get breakdown of test cases by type (scoped)."""
    scope_all, user_ids = scope
    effective_ids = None if scope_all else user_ids

    breakdown = await AnalyticsService.get_test_case_breakdown(effective_ids, db)
    return TestCaseBreakdownResponse(**breakdown)
