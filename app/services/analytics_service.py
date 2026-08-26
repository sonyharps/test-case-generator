from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Integer, case, and_
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.models.session import OrchestratorSession
from app.models.test_case import TestCaseRecord


class AnalyticsService:
    """Service for calculating user analytics from session data.

    All methods accept a ``scope`` parameter — either a list of user_ids
    (``user_ids``) to filter on, or ``None`` meaning "all users" (kabag/admin).
    """

    @staticmethod
    def _user_filter(user_ids: Optional[List[int]]):
        """Build a WHERE clause for the scoped user set.

        ``None`` → no filter (see all). ``[1,2,3]`` → IN (1,2,3).
        """
        if user_ids is None:
            return None
        return OrchestratorSession.user_id.in_(user_ids)

    @staticmethod
    def _apply(base_stmt, user_ids: Optional[List[int]]):
        filt = AnalyticsService._user_filter(user_ids)
        return base_stmt.where(filt) if filt is not None else base_stmt

    @staticmethod
    async def get_user_stats(user_ids: Optional[List[int]], db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive analytics for the scoped user set."""
        # Total sessions
        total_sessions_result = await db.execute(
            AnalyticsService._apply(
                select(func.count(OrchestratorSession.id)), user_ids
            )
        )
        total_sessions = total_sessions_result.scalar() or 0

        # Total test cases
        total_tc_result = await db.execute(
            AnalyticsService._apply(
                select(func.count(TestCaseRecord.id)).join(
                    OrchestratorSession, TestCaseRecord.session_id == OrchestratorSession.id
                ),
                user_ids,
            )
        )
        total_test_cases = total_tc_result.scalar() or 0

        # Breakdown by type
        breakdown_result = await db.execute(
            AnalyticsService._apply(
                select(
                    TestCaseRecord.tc_type,
                    func.count(TestCaseRecord.id).label("count"),
                ).join(OrchestratorSession, TestCaseRecord.session_id == OrchestratorSession.id),
                user_ids,
            ).group_by(TestCaseRecord.tc_type)
        )
        tc_breakdown = {"functional": 0, "negative": 0, "boundary": 0}
        for row in breakdown_result:
            tc_breakdown[row.tc_type] = row.count

        # Average execution time
        avg_stmt = select(func.avg(OrchestratorSession.execution_time_ms)).where(
            OrchestratorSession.execution_time_ms.isnot(None)
        )
        avg_stmt = AnalyticsService._apply(avg_stmt, user_ids)
        avg_execution_time = (await db.execute(avg_stmt)).scalar()

        # Most used model
        most_used_stmt = AnalyticsService._apply(
            select(
                OrchestratorSession.model_used,
                func.count(OrchestratorSession.id).label("count"),
            ),
            user_ids,
        ).group_by(OrchestratorSession.model_used).order_by(
            func.count(OrchestratorSession.id).desc()
        ).limit(1)
        most_used_model_row = (await db.execute(most_used_stmt)).first()
        most_used_model = most_used_model_row[0] if most_used_model_row else None

        # Sessions in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sessions_30d_stmt = select(func.count(OrchestratorSession.id)).where(
            OrchestratorSession.created_at >= thirty_days_ago
        )
        sessions_30d_stmt = AnalyticsService._apply(sessions_30d_stmt, user_ids)
        sessions_last_30_days = (await db.execute(sessions_30d_stmt)).scalar() or 0

        return {
            "total_sessions": total_sessions,
            "total_test_cases": total_test_cases,
            "total_functional": tc_breakdown["functional"],
            "total_negative": tc_breakdown["negative"],
            "total_boundary": tc_breakdown["boundary"],
            "avg_execution_time_ms": int(avg_execution_time) if avg_execution_time else 0,
            "most_used_model": most_used_model,
            "sessions_last_30_days": sessions_last_30_days,
        }

    @staticmethod
    async def get_sessions_timeline(
        user_ids: Optional[List[int]],
        db: AsyncSession,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get sessions grouped by date for timeline chart."""
        start_date = datetime.utcnow() - timedelta(days=days)

        stmt = select(
            func.date(OrchestratorSession.created_at).label("date"),
            func.count(OrchestratorSession.id).label("count"),
        ).where(OrchestratorSession.created_at >= start_date)
        stmt = AnalyticsService._apply(stmt, user_ids)
        stmt = stmt.group_by(func.date(OrchestratorSession.created_at)).order_by(
            func.date(OrchestratorSession.created_at)
        )

        result = await db.execute(stmt)
        return [{"date": row.date.isoformat(), "count": row.count} for row in result]

    @staticmethod
    async def get_model_usage(
        user_ids: Optional[List[int]], db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get breakdown of sessions by model."""
        stmt = AnalyticsService._apply(
            select(
                OrchestratorSession.model_used,
                func.count(OrchestratorSession.id).label("count"),
            ),
            user_ids,
        ).group_by(OrchestratorSession.model_used).order_by(
            func.count(OrchestratorSession.id).desc()
        )

        result = await db.execute(stmt)
        return [{"model": row.model_used, "count": row.count} for row in result]

    @staticmethod
    async def get_test_case_breakdown(
        user_ids: Optional[List[int]], db: AsyncSession
    ) -> Dict[str, int]:
        """Get breakdown of test cases by type across all sessions."""
        stmt = AnalyticsService._apply(
            select(
                TestCaseRecord.tc_type,
                func.count(TestCaseRecord.id).label("count"),
            ).join(OrchestratorSession, TestCaseRecord.session_id == OrchestratorSession.id),
            user_ids,
        ).group_by(TestCaseRecord.tc_type)

        result = await db.execute(stmt)
        breakdown = {"functional": 0, "negative": 0, "boundary": 0}
        for row in result:
            breakdown[row.tc_type] = row.count
        return breakdown
