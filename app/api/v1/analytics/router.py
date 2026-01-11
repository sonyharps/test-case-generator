from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps.auth import get_current_active_user
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
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive user statistics

    Returns:
    - Total sessions created
    - Total test cases generated (with breakdown by type)
    - Average execution time
    - Most used model
    - Recent activity (last 30 days)
    """
    logger.info("Fetching user statistics", user_id=current_user.id)

    stats = await AnalyticsService.get_user_stats(current_user.id, db)

    return UserStatsResponse(**stats)


@router.get("/timeline", response_model=TimelineResponse)
async def get_sessions_timeline(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get sessions grouped by date for timeline visualization

    Useful for creating line/bar charts showing session activity over time
    """
    logger.info("Fetching timeline data", user_id=current_user.id, days=days)

    timeline_data = await AnalyticsService.get_sessions_timeline(
        current_user.id, db, days
    )

    timeline_points = [TimelineDataPoint(**point) for point in timeline_data]

    return TimelineResponse(timeline=timeline_points, days=days)


@router.get("/models", response_model=ModelUsageResponse)
async def get_model_usage(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get breakdown of sessions by model used

    Returns list of models with usage counts, ordered by most used
    Useful for pie/donut charts
    """
    logger.info("Fetching model usage data", user_id=current_user.id)

    model_data = await AnalyticsService.get_model_usage(current_user.id, db)

    model_points = [ModelUsageDataPoint(**point) for point in model_data]

    return ModelUsageResponse(model_usage=model_points)


@router.get("/test-cases/breakdown", response_model=TestCaseBreakdownResponse)
async def get_test_case_breakdown(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get breakdown of test cases by type (functional, negative, boundary)

    Useful for pie/donut charts showing test case distribution
    """
    logger.info("Fetching test case breakdown", user_id=current_user.id)

    breakdown = await AnalyticsService.get_test_case_breakdown(current_user.id, db)

    return TestCaseBreakdownResponse(**breakdown)
