from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Dict, Any

from app.db.session import get_db
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from app.models.session import OrchestratorSession
from app.models.test_case import TestCaseRecord, TestCaseType
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get dashboard statistics for the current user

    Returns:
    - total_sessions: Total number of sessions created
    - total_test_cases: Total number of test cases generated
    - avg_execution_time: Average execution time in milliseconds
    - last_generation_date: Date of the last session
    - test_case_distribution: Count by type (functional, negative, boundary)
    - approval_stats: Counts by status (draft, approved, rejected)
    - recent_activity: Last 7 days activity
    """
    logger.info("Fetching dashboard stats", user_id=current_user.id)

    # Total sessions
    total_sessions_query = select(func.count(OrchestratorSession.id)).where(
        OrchestratorSession.user_id == current_user.id
    )
    total_sessions_result = await db.execute(total_sessions_query)
    total_sessions = total_sessions_result.scalar() or 0

    # Total test cases
    total_tc_query = select(func.count(TestCaseRecord.id)).join(
        OrchestratorSession, TestCaseRecord.session_id == OrchestratorSession.id
    ).where(OrchestratorSession.user_id == current_user.id)
    total_tc_result = await db.execute(total_tc_query)
    total_test_cases = total_tc_result.scalar() or 0

    # Average execution time
    avg_time_query = select(func.avg(OrchestratorSession.execution_time_ms)).where(
        OrchestratorSession.user_id == current_user.id
    )
    avg_time_result = await db.execute(avg_time_query)
    avg_execution_time = avg_time_result.scalar() or 0

    # Last generation date
    last_session_query = select(OrchestratorSession.created_at).where(
        OrchestratorSession.user_id == current_user.id
    ).order_by(OrchestratorSession.created_at.desc()).limit(1)
    last_session_result = await db.execute(last_session_query)
    last_generation = last_session_result.scalar_one_or_none()

    # Test case distribution by type
    distribution_query = select(
        TestCaseRecord.tc_type,
        func.count(TestCaseRecord.id).label("count")
    ).join(
        OrchestratorSession, TestCaseRecord.session_id == OrchestratorSession.id
    ).where(
        OrchestratorSession.user_id == current_user.id
    ).group_by(TestCaseRecord.tc_type)

    distribution_result = await db.execute(distribution_query)
    distribution_rows = distribution_result.all()

    test_case_distribution = {
        "functional": 0,
        "negative": 0,
        "boundary": 0
    }
    for tc_type, count in distribution_rows:
        test_case_distribution[tc_type.value] = count

    # Approval statistics
    approval_query = select(
        TestCaseRecord.status,
        func.count(TestCaseRecord.id).label("count")
    ).join(
        OrchestratorSession, TestCaseRecord.session_id == OrchestratorSession.id
    ).where(
        OrchestratorSession.user_id == current_user.id
    ).group_by(TestCaseRecord.status)

    approval_result = await db.execute(approval_query)
    approval_rows = approval_result.all()

    approval_stats = {
        "draft": 0,
        "approved": 0,
        "rejected": 0
    }
    for status, count in approval_rows:
        approval_stats[status] = count

    # Recent activity (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_activity_query = select(
        func.date(OrchestratorSession.created_at).label("date"),
        func.count(OrchestratorSession.id).label("count")
    ).where(
        OrchestratorSession.user_id == current_user.id,
        OrchestratorSession.created_at >= seven_days_ago
    ).group_by(func.date(OrchestratorSession.created_at)).order_by(func.date(OrchestratorSession.created_at))

    recent_activity_result = await db.execute(recent_activity_query)
    recent_activity_rows = recent_activity_result.all()

    recent_activity = [
        {"date": row.date.isoformat(), "count": row.count}
        for row in recent_activity_rows
    ]

    logger.info(
        "Dashboard stats fetched successfully",
        user_id=current_user.id,
        total_sessions=total_sessions,
        total_test_cases=total_test_cases
    )

    return {
        "total_sessions": total_sessions,
        "total_test_cases": total_test_cases,
        "avg_execution_time_ms": int(avg_execution_time) if avg_execution_time else 0,
        "last_generation_date": last_generation.isoformat() if last_generation else None,
        "test_case_distribution": test_case_distribution,
        "approval_stats": approval_stats,
        "recent_activity": recent_activity
    }
