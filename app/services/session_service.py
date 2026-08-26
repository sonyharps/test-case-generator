import uuid
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.session import OrchestratorSession
from app.models.test_case import TestCaseRecord, TestCaseType

class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        user_id: int,
        requirement_text: str,
        model_used: str,
        generate_boundary: bool,
        include_risk: bool,
        result: Dict[str, Any],
        execution_time_ms: int
    ) -> OrchestratorSession:
        """Create new orchestrator session with test cases"""

        # Create session
        session = OrchestratorSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            requirement_text=requirement_text,
            model_used=model_used,
            generate_boundary=generate_boundary,
            include_risk=include_risk,
            summary=result.get("summary"),
            coverage_matrix=result.get("coverage_matrix"),
            risk_assessment=result.get("risk"),
            session_metadata=result.get("metadata"),
            execution_time_ms=execution_time_ms
        )
        self.db.add(session)
        await self.db.flush()  # Get session.id

        # Create test case records (including ISO/IEC/IEEE 29119-3 extended fields)
        def _tc_fields(tc: dict) -> dict:
            return {
                "priority": tc.get("priority"),
                "module": tc.get("module"),
                "test_data": tc.get("test_data"),
                "postconditions": tc.get("postconditions"),
            }

        for tc in result.get("functional", []):
            tc_record = TestCaseRecord(
                session_id=session.id,
                tc_id=tc["tc_id"],
                tc_type=TestCaseType.FUNCTIONAL,
                title=tc["title"],
                preconditions=tc["preconditions"],
                steps=tc["steps"],
                expected_result=tc["expected_result"],
                **_tc_fields(tc),
            )
            self.db.add(tc_record)

        for tc in result.get("negative", []):
            tc_record = TestCaseRecord(
                session_id=session.id,
                tc_id=tc["tc_id"],
                tc_type=TestCaseType.NEGATIVE,
                title=tc["title"],
                preconditions=tc["preconditions"],
                steps=tc["steps"],
                expected_result=tc["expected_result"],
                **_tc_fields(tc),
            )
            self.db.add(tc_record)

        for tc in result.get("boundary", []):
            tc_record = TestCaseRecord(
                session_id=session.id,
                tc_id=tc["tc_id"],
                tc_type=TestCaseType.BOUNDARY,
                title=tc["title"],
                preconditions=tc["preconditions"],
                steps=tc["steps"],
                expected_result=tc["expected_result"],
                **_tc_fields(tc),
            )
            self.db.add(tc_record)

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_user_sessions(self, user_id: int, limit: int = 20) -> List[OrchestratorSession]:
        """Get user's recent sessions"""
        result = await self.db.execute(
            select(OrchestratorSession)
            .where(OrchestratorSession.user_id == user_id)
            .order_by(OrchestratorSession.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_session_by_id(self, session_id: str, user_id: int) -> OrchestratorSession:
        """Get specific session by ID for a user"""
        result = await self.db.execute(
            select(OrchestratorSession)
            .where(
                OrchestratorSession.session_id == session_id,
                OrchestratorSession.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
