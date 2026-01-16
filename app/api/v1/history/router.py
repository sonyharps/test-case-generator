from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.db.session import get_db
from app.models.user import User
from app.models.session import OrchestratorSession
from app.models.test_case import TestCaseRecord
from app.models.test_repository import RepositoryTestCase, Project, TestSuite
from app.api.deps.auth import get_current_active_user
from app.schemas.session_schema import SessionListResponse, SessionDetailResponse, TestCaseResponse
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/sessions", response_model=SessionListResponse)
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return")
):
    """
    Get user's orchestrator session history

    Returns paginated list of sessions with metadata:
    - session_id: UUID for the session
    - requirement_text: Original requirement
    - model_used: LLM model name
    - execution_time_ms: How long generation took
    - created_at: When the session was created
    - test_case_count: Total number of test cases generated
    """
    logger.info("Fetching user sessions", user_id=current_user.id, skip=skip, limit=limit)

    # Get total count
    count_query = select(func.count(OrchestratorSession.id)).where(
        OrchestratorSession.user_id == current_user.id
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get sessions with test case counts
    query = (
        select(
            OrchestratorSession,
            func.count(TestCaseRecord.id).label("test_case_count")
        )
        .outerjoin(TestCaseRecord, TestCaseRecord.session_id == OrchestratorSession.id)
        .where(OrchestratorSession.user_id == current_user.id)
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
            "test_case_count": test_case_count
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
    """
    Get detailed session information including all test cases

    Returns:
    - Session metadata
    - All functional, negative, and boundary test cases
    - Summary and risk assessment
    - Coverage matrix
    """
    logger.info("Fetching session detail", user_id=current_user.id, session_id=session_id)

    # Get session
    session_query = select(OrchestratorSession).where(
        OrchestratorSession.session_id == session_id,
        OrchestratorSession.user_id == current_user.id
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        logger.warning("Session not found", user_id=current_user.id, session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Get all test cases for this session (eager load editor relationship)
    tc_query = select(TestCaseRecord).options(
        selectinload(TestCaseRecord.editor)
    ).where(
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
            "status": tc.status,  # Phase 2: approval status
            "edit_count": tc.edit_count,
            "edited_by": getattr(tc.editor, 'username', None) if tc.editor else None,
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

    return SessionDetailResponse(
        session_id=session.session_id,
        requirement_text=session.requirement_text,
        model_used=session.model_used,
        generate_boundary=session.generate_boundary,
        include_risk=session.include_risk,
        execution_time_ms=session.execution_time_ms,
        created_at=session.created_at,
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
    """
    Delete a session and all associated test cases

    This will permanently remove:
    - The session record
    - All test cases in the session (cascade delete)
    """
    logger.info("Deleting session", user_id=current_user.id, session_id=session_id)

    # Get session
    session_query = select(OrchestratorSession).where(
        OrchestratorSession.session_id == session_id,
        OrchestratorSession.user_id == current_user.id
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        logger.warning("Session not found for deletion", user_id=current_user.id, session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Delete session (test cases will be deleted via cascade)
    await db.delete(session)
    await db.commit()

    logger.info("Session deleted successfully", user_id=current_user.id, session_id=session_id)
    return None


@router.get("/sessions/{session_id}/repository-link")
async def get_session_repository_link(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get repository link information for a session

    Returns:
    - is_saved: Whether the session has been saved to repository
    - project_id: ID of the project (if saved)
    - project_name: Name of the project (if saved)
    - suite_id: ID of the suite (if saved)
    - suite_name: Name of the suite (if saved)
    - test_case_count: Number of test cases in repository from this session
    """
    logger.info("Fetching session repository link", user_id=current_user.id, session_id=session_id)

    # Verify session exists and belongs to user
    session_query = select(OrchestratorSession).where(
        OrchestratorSession.session_id == session_id,
        OrchestratorSession.user_id == current_user.id
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Check for repository test cases with this source_session_id
    repo_query = (
        select(RepositoryTestCase, TestSuite, Project)
        .join(TestSuite, RepositoryTestCase.suite_id == TestSuite.id)
        .join(Project, TestSuite.project_id == Project.id)
        .where(RepositoryTestCase.source_session_id == session_id)
    )
    repo_result = await db.execute(repo_query)
    repo_rows = repo_result.all()

    if not repo_rows:
        return {
            "is_saved": False,
            "project_id": None,
            "project_name": None,
            "suite_id": None,
            "suite_name": None,
            "test_case_count": 0
        }

    # Get the first row's project/suite info (all test cases from same session should be in same suite)
    first_tc, suite, project = repo_rows[0]

    return {
        "is_saved": True,
        "project_id": project.id,
        "project_name": project.name,
        "suite_id": suite.id,
        "suite_name": suite.name,
        "test_case_count": len(repo_rows)
    }
