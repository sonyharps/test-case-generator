from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Integer, case
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.models.session import OrchestratorSession
from app.models.test_case import TestCaseRecord


class AnalyticsService:
    """Service for calculating user analytics from session data"""

    @staticmethod
    async def get_user_stats(user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a user

        Returns:
        - total_sessions: Number of sessions created
        - total_test_cases: Total test cases generated
        - avg_execution_time: Average execution time in ms
        - total_functional: Total functional test cases
        - total_negative: Total negative test cases
        - total_boundary: Total boundary test cases
        - most_used_model: Most frequently used model
        - sessions_last_30_days: Number of sessions in last 30 days
        """
        # Get total sessions
        total_sessions_result = await db.execute(
            select(func.count(OrchestratorSession.id))
            .where(OrchestratorSession.user_id == user_id)
        )
        total_sessions = total_sessions_result.scalar() or 0

        # Get total test cases
        total_tc_result = await db.execute(
            select(func.count(TestCaseRecord.id))
            .join(OrchestratorSession, TestCaseRecord.session_id == OrchestratorSession.id)
            .where(OrchestratorSession.user_id == user_id)
        )
        total_test_cases = total_tc_result.scalar() or 0

        # Get breakdown by type
        breakdown_result = await db.execute(
            select(
                TestCaseRecord.tc_type,
                func.count(TestCaseRecord.id).label("count")
            )
            .join(OrchestratorSession, TestCaseRecord.session_id == OrchestratorSession.id)
            .where(OrchestratorSession.user_id == user_id)
            .group_by(TestCaseRecord.tc_type)
        )

        tc_breakdown = {"functional": 0, "negative": 0, "boundary": 0}
        for row in breakdown_result:
            tc_breakdown[row.tc_type] = row.count

        # Get average execution time
        avg_time_result = await db.execute(
            select(func.avg(OrchestratorSession.execution_time_ms))
            .where(
                OrchestratorSession.user_id == user_id,
                OrchestratorSession.execution_time_ms.isnot(None)
            )
        )
        avg_execution_time = avg_time_result.scalar()

        # Get most used model
        most_used_model_result = await db.execute(
            select(
                OrchestratorSession.model_used,
                func.count(OrchestratorSession.id).label("count")
            )
            .where(OrchestratorSession.user_id == user_id)
            .group_by(OrchestratorSession.model_used)
            .order_by(func.count(OrchestratorSession.id).desc())
            .limit(1)
        )
        most_used_model_row = most_used_model_result.first()
        most_used_model = most_used_model_row[0] if most_used_model_row else None

        # Get sessions in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sessions_30d_result = await db.execute(
            select(func.count(OrchestratorSession.id))
            .where(
                OrchestratorSession.user_id == user_id,
                OrchestratorSession.created_at >= thirty_days_ago
            )
        )
        sessions_last_30_days = sessions_30d_result.scalar() or 0

        return {
            "total_sessions": total_sessions,
            "total_test_cases": total_test_cases,
            "total_functional": tc_breakdown["functional"],
            "total_negative": tc_breakdown["negative"],
            "total_boundary": tc_breakdown["boundary"],
            "avg_execution_time_ms": int(avg_execution_time) if avg_execution_time else 0,
            "most_used_model": most_used_model,
            "sessions_last_30_days": sessions_last_30_days
        }

    @staticmethod
    async def get_sessions_timeline(
        user_id: int,
        db: AsyncSession,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get sessions grouped by date for timeline chart

        Returns list of {"date": "2024-01-01", "count": 5}
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(
                func.date(OrchestratorSession.created_at).label("date"),
                func.count(OrchestratorSession.id).label("count")
            )
            .where(
                OrchestratorSession.user_id == user_id,
                OrchestratorSession.created_at >= start_date
            )
            .group_by(func.date(OrchestratorSession.created_at))
            .order_by(func.date(OrchestratorSession.created_at))
        )

        timeline = []
        for row in result:
            timeline.append({
                "date": row.date.isoformat(),
                "count": row.count
            })

        return timeline

    @staticmethod
    async def get_model_usage(user_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Get breakdown of sessions by model

        Returns list of {"model": "llama3.1:8b", "count": 15}
        """
        result = await db.execute(
            select(
                OrchestratorSession.model_used,
                func.count(OrchestratorSession.id).label("count")
            )
            .where(OrchestratorSession.user_id == user_id)
            .group_by(OrchestratorSession.model_used)
            .order_by(func.count(OrchestratorSession.id).desc())
        )

        model_usage = []
        for row in result:
            model_usage.append({
                "model": row.model_used,
                "count": row.count
            })

        return model_usage

    @staticmethod
    async def get_test_case_breakdown(user_id: int, db: AsyncSession) -> Dict[str, int]:
        """
        Get breakdown of test cases by type across all sessions

        Returns: {"functional": 50, "negative": 30, "boundary": 20}
        """
        result = await db.execute(
            select(
                TestCaseRecord.tc_type,
                func.count(TestCaseRecord.id).label("count")
            )
            .join(OrchestratorSession, TestCaseRecord.session_id == OrchestratorSession.id)
            .where(OrchestratorSession.user_id == user_id)
            .group_by(TestCaseRecord.tc_type)
        )

        breakdown = {"functional": 0, "negative": 0, "boundary": 0}
        for row in result:
            breakdown[row.tc_type] = row.count

        return breakdown
