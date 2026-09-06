from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from sqlalchemy import select, func
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.session import OrchestratorSession
from app.models.test_case import TestCaseRecord
from app.api.deps.auth import get_current_active_user, get_data_scope, can_access_session
from app.schemas.session_schema import SessionListResponse, SessionDetailResponse, TestCaseResponse
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/sessions", response_model=SessionListResponse)
async def get_user_sessions(
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    scope: tuple = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return")
):
    """
    Get orchestrator session history for the caller's data scope.

    qa_staff → own sessions. qa_lead → squad sessions. kabag/admin → all sessions.
    """
    scope_all, user_ids = scope
    logger.info("Fetching sessions", user_id=current_user.id, scope_all=scope_all, skip=skip, limit=limit)

    # Build user filter
    user_filt = None if scope_all else OrchestratorSession.user_id.in_(user_ids)

    # Get total count
    count_query = select(func.count(OrchestratorSession.id))
    if user_filt is not None:
        count_query = count_query.where(user_filt)
    if project_id is not None:
        count_query = count_query.where(OrchestratorSession.project_id == project_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get sessions with test case counts
    query = (
        select(
            OrchestratorSession,
            func.count(TestCaseRecord.id).label("test_case_count")
        )
        .outerjoin(TestCaseRecord, TestCaseRecord.session_id == OrchestratorSession.id)
    )
    if user_filt is not None:
        query = query.where(user_filt)
    if project_id is not None:
        query = query.where(OrchestratorSession.project_id == project_id)
    query = (
        query
        .group_by(OrchestratorSession.id)
        .order_by(OrchestratorSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    sessions = []
    for session, test_case_count in rows:
        sessions.append({
            "id": session.id,
            "session_id": session.session_id,
            "requirement_text": session.requirement_text,
            "model_used": session.model_used,
            "generate_boundary": session.generate_boundary,
            "include_risk": session.include_risk,
            "execution_time_ms": session.execution_time_ms,
            "created_at": session.created_at,
            "test_case_count": test_case_count,
            "drive_file_link": session.drive_file_link,
            "project_id": session.project_id
        })

    logger.info("Sessions fetched successfully", user_id=current_user.id, count=len(sessions))

    return SessionListResponse(
        sessions=sessions,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed session information including all test cases.

    Access honored per role + squad scope (can_access_session).
    """
    logger.info("Fetching session detail", user_id=current_user.id, session_id=session_id)

    # Get session (without ownership filter — we check scope below)
    session_query = select(OrchestratorSession).where(
        OrchestratorSession.session_id == session_id,
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        logger.warning("Session not found", user_id=current_user.id, session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # RBAC: ensure caller may view this session
    if not await can_access_session(session.user_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session"
        )

    # Get all test cases for this session
    tc_query = select(TestCaseRecord).where(
        TestCaseRecord.session_id == session.id
    ).order_by(TestCaseRecord.tc_id)
    tc_result = await db.execute(tc_query)
    test_cases = tc_result.scalars().all()

    # Group test cases by type
    functional = []
    negative = []
    boundary = []

    for tc in test_cases:
        tc_data = {
            "id": tc.id,  # Database ID for editing
            "tc_id": tc.tc_id,
            "title": tc.title,
            "preconditions": tc.preconditions,
            "steps": tc.steps,
            "expected_result": tc.expected_result,
            "priority": tc.priority,
            "module": tc.module,
            "test_data": tc.test_data,
            "postconditions": tc.postconditions,
            "status": tc.status,  # Phase 2: approval status
            "edit_count": tc.edit_count,
            "edited_by": tc.editor.username if tc.editor else None,
            "edited_at": tc.edited_at.isoformat() if tc.edited_at else None,
        }

        if tc.tc_type.value == "functional":
            functional.append(tc_data)
        elif tc.tc_type.value == "negative":
            negative.append(tc_data)
        elif tc.tc_type.value == "boundary":
            boundary.append(tc_data)

    logger.info("Session detail fetched", user_id=current_user.id, session_id=session_id,
                functional_count=len(functional), negative_count=len(negative), boundary_count=len(boundary))

    project_name = None
    if session.project_id:
        from app.models.project import Project
        proj_row = await db.execute(select(Project.name).where(Project.id == session.project_id))
        project_name = proj_row.scalar()

    return SessionDetailResponse(
        session_id=session.session_id,
        project_id=session.project_id,
        project_name=project_name,
        requirement_text=session.requirement_text,
        model_used=session.model_used,
        generate_boundary=session.generate_boundary,
        include_risk=session.include_risk,
        execution_time_ms=session.execution_time_ms,
        created_at=session.created_at,
        drive_file_link=session.drive_file_link,
        functional=functional,
        negative=negative,
        boundary=boundary,
        summary=session.summary,
        risk=session.risk_assessment,
        coverage_matrix=session.coverage_matrix,
        metadata=session.session_metadata
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a session and all associated test cases.

    Access honored per role + squad scope (can_access_session).
    """
    logger.info("Deleting session", user_id=current_user.id, session_id=session_id)

    # Get session without ownership filter
    session_query = select(OrchestratorSession).where(
        OrchestratorSession.session_id == session_id,
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        logger.warning("Session not found for deletion", user_id=current_user.id, session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # RBAC
    if not await can_access_session(session.user_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session"
        )

    # Delete session (test cases will be deleted via cascade)
    await db.delete(session)
    await db.commit()

    logger.info("Session deleted successfully", user_id=current_user.id, session_id=session_id)
    return None
