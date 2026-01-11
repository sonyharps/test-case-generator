from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from app.models.test_case import TestCaseRecord, TestCaseStatus
from app.models.comment import TestCaseComment
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Pydantic schemas
class TestCaseEditRequest(BaseModel):
    title: Optional[str] = None
    preconditions: Optional[List[str]] = None
    steps: Optional[List[str]] = None
    expected_result: Optional[List[str]] = None


class TestCaseApprovalRequest(BaseModel):
    status: TestCaseStatus
    rejection_reason: Optional[str] = None


class CommentCreate(BaseModel):
    comment_text: str = Field(..., min_length=1, max_length=5000)
    parent_comment_id: Optional[int] = None


class CommentResponse(BaseModel):
    id: int
    test_case_id: int
    user_id: int
    user_name: str
    comment_text: str
    parent_comment_id: Optional[int]
    is_resolved: bool
    created_at: datetime
    replies: List['CommentResponse'] = []

    class Config:
        from_attributes = True


# Recursively handle nested comments
CommentResponse.model_rebuild()


@router.get("/test-cases/{test_case_id}")
async def get_test_case(
    test_case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed test case information including status and edit history
    """
    result = await db.execute(
        select(TestCaseRecord).where(TestCaseRecord.id == test_case_id)
    )
    test_case = result.scalar_one_or_none()

    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    # Verify user has access to this test case (via session ownership)
    session_result = await db.execute(
        select(TestCaseRecord).where(
            TestCaseRecord.id == test_case_id,
            TestCaseRecord.session.has(user_id=current_user.id)
        )
    )
    if not session_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to this test case")

    return {
        "id": test_case.id,
        "tc_id": test_case.tc_id,
        "title": test_case.title,
        "preconditions": test_case.preconditions,
        "steps": test_case.steps,
        "expected_result": test_case.expected_result,
        "status": test_case.status,
        "tc_type": test_case.tc_type,
        "edit_count": test_case.edit_count,
        "edited_by": test_case.editor.username if test_case.editor else None,
        "edited_at": test_case.edited_at,
        "approved_by": test_case.approver.username if test_case.approver else None,
        "approved_at": test_case.approved_at,
        "rejection_reason": test_case.rejection_reason,
        "original_content": test_case.original_content,
        "created_at": test_case.created_at,
        "updated_at": test_case.updated_at
    }


@router.patch("/test-cases/{test_case_id}")
async def edit_test_case(
    test_case_id: int,
    edit_request: TestCaseEditRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Edit a test case (inline editing)

    Tracks edit history and preserves original AI-generated content
    """
    # Fetch test case
    result = await db.execute(
        select(TestCaseRecord).where(TestCaseRecord.id == test_case_id)
    )
    test_case = result.scalar_one_or_none()

    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    # Verify ownership
    from app.models.session import OrchestratorSession
    session_result = await db.execute(
        select(OrchestratorSession).where(
            OrchestratorSession.id == test_case.session_id,
            OrchestratorSession.user_id == current_user.id
        )
    )
    if not session_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to edit this test case")

    # Store original content on first edit
    if test_case.edit_count == 0:
        test_case.original_content = {
            "title": test_case.title,
            "preconditions": test_case.preconditions,
            "steps": test_case.steps,
            "expected_result": test_case.expected_result
        }

    # Apply edits
    if edit_request.title is not None:
        test_case.title = edit_request.title
    if edit_request.preconditions is not None:
        test_case.preconditions = edit_request.preconditions
    if edit_request.steps is not None:
        test_case.steps = edit_request.steps
    if edit_request.expected_result is not None:
        test_case.expected_result = edit_request.expected_result

    # Update edit tracking
    test_case.edited_by = current_user.id
    test_case.edited_at = datetime.utcnow()
    test_case.edit_count += 1

    await db.commit()
    await db.refresh(test_case)

    logger.info(
        "test_case_edited",
        test_case_id=test_case_id,
        user_id=current_user.id,
        edit_count=test_case.edit_count
    )

    return {
        "message": "Test case updated successfully",
        "test_case_id": test_case.id,
        "edit_count": test_case.edit_count
    }


@router.post("/test-cases/{test_case_id}/approval")
async def update_test_case_approval(
    test_case_id: int,
    approval_request: TestCaseApprovalRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve or reject a test case

    QA engineers can approve/reject generated test cases
    """
    # Fetch test case
    result = await db.execute(
        select(TestCaseRecord).where(TestCaseRecord.id == test_case_id)
    )
    test_case = result.scalar_one_or_none()

    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    # Verify ownership
    from app.models.session import OrchestratorSession
    session_result = await db.execute(
        select(OrchestratorSession).where(
            OrchestratorSession.id == test_case.session_id,
            OrchestratorSession.user_id == current_user.id
        )
    )
    if not session_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to approve this test case")

    # Validate rejection reason
    if approval_request.status == TestCaseStatus.REJECTED and not approval_request.rejection_reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required when rejecting a test case")

    # Update approval status
    test_case.status = approval_request.status
    test_case.approved_by = current_user.id
    test_case.approved_at = datetime.utcnow()
    test_case.rejection_reason = approval_request.rejection_reason if approval_request.status == TestCaseStatus.REJECTED else None

    await db.commit()
    await db.refresh(test_case)

    logger.info(
        "test_case_approval_updated",
        test_case_id=test_case_id,
        status=approval_request.status,
        user_id=current_user.id
    )

    return {
        "message": f"Test case {approval_request.status.value} successfully",
        "test_case_id": test_case.id,
        "status": test_case.status
    }


@router.post("/test-cases/{test_case_id}/comments")
async def add_comment(
    test_case_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a comment to a test case

    Supports threaded comments via parent_comment_id
    """
    # Verify test case exists and user has access
    result = await db.execute(
        select(TestCaseRecord).where(TestCaseRecord.id == test_case_id)
    )
    test_case = result.scalar_one_or_none()

    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    # Verify ownership
    from app.models.session import OrchestratorSession
    session_result = await db.execute(
        select(OrchestratorSession).where(
            OrchestratorSession.id == test_case.session_id,
            OrchestratorSession.user_id == current_user.id
        )
    )
    if not session_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to comment on this test case")

    # Verify parent comment exists if provided
    if comment_data.parent_comment_id:
        parent_result = await db.execute(
            select(TestCaseComment).where(
                TestCaseComment.id == comment_data.parent_comment_id,
                TestCaseComment.test_case_id == test_case_id
            )
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Parent comment not found")

    # Create comment
    comment = TestCaseComment(
        test_case_id=test_case_id,
        user_id=current_user.id,
        comment_text=comment_data.comment_text,
        parent_comment_id=comment_data.parent_comment_id
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    logger.info(
        "comment_added",
        test_case_id=test_case_id,
        comment_id=comment.id,
        user_id=current_user.id
    )

    return {
        "message": "Comment added successfully",
        "comment_id": comment.id,
        "created_at": comment.created_at
    }


@router.get("/test-cases/{test_case_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    test_case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all comments for a test case (with threading support)
    """
    # Verify test case exists and user has access
    result = await db.execute(
        select(TestCaseRecord).where(TestCaseRecord.id == test_case_id)
    )
    test_case = result.scalar_one_or_none()

    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    # Get all comments for this test case
    comments_result = await db.execute(
        select(TestCaseComment)
        .where(TestCaseComment.test_case_id == test_case_id)
        .order_by(TestCaseComment.created_at.asc())
    )
    comments = comments_result.scalars().all()

    # Build threaded comment structure
    comment_dict = {}
    root_comments = []

    for comment in comments:
        comment_data = {
            "id": comment.id,
            "test_case_id": comment.test_case_id,
            "user_id": comment.user_id,
            "user_name": comment.user.username if comment.user else "Unknown",
            "comment_text": comment.comment_text,
            "parent_comment_id": comment.parent_comment_id,
            "is_resolved": comment.is_resolved,
            "created_at": comment.created_at,
            "replies": []
        }
        comment_dict[comment.id] = comment_data

        if comment.parent_comment_id is None:
            root_comments.append(comment_data)
        else:
            if comment.parent_comment_id in comment_dict:
                comment_dict[comment.parent_comment_id]["replies"].append(comment_data)

    return root_comments


@router.patch("/test-cases/{test_case_id}/comments/{comment_id}/resolve")
async def resolve_comment(
    test_case_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a comment as resolved
    """
    result = await db.execute(
        select(TestCaseComment).where(
            TestCaseComment.id == comment_id,
            TestCaseComment.test_case_id == test_case_id
        )
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.is_resolved = True
    await db.commit()

    logger.info(
        "comment_resolved",
        comment_id=comment_id,
        user_id=current_user.id
    )

    return {"message": "Comment marked as resolved"}
