"""Test Runs API Router

Endpoints for managing test runs and test execution results
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from datetime import datetime
import os
import uuid
import aiofiles
from pathlib import Path
from io import BytesIO

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from app.db.session import get_db
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from app.models.test_repository import (
    Project,
    TestSuite,
    RepositoryTestCase,
    TestRun,
    TestResult,
    TestRunStatus,
    TestResultStatus,
    Milestone,
)
from app.schemas.test_repository_schema import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse,
    MilestoneListResponse,
    TestRunCreate,
    TestRunUpdate,
    TestRunResponse,
    TestRunListResponse,
    TestRunWithResultsResponse,
    TestResultCreate,
    TestResultUpdate,
    TestResultResponse,
    TestResultListResponse,
    BulkResultUpdate,
    BulkResultUpdateResponse,
    RepositoryTestCaseResponse,
    EvidenceItem,
)
from app.core.logging_config import get_logger
from app.core.config import settings

router = APIRouter()
logger = get_logger(__name__)


# =====================================================
# MILESTONES
# =====================================================

@router.post("/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    milestone_data: MilestoneCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new milestone"""
    logger.info("Creating milestone", user_id=current_user.id, name=milestone_data.name)

    # Verify project exists
    project_result = await db.execute(select(Project).where(Project.id == milestone_data.project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    milestone = Milestone(
        name=milestone_data.name,
        description=milestone_data.description,
        project_id=milestone_data.project_id,
        due_date=milestone_data.due_date,
        created_by_id=current_user.id
    )

    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)

    logger.info("Milestone created", user_id=current_user.id, milestone_id=milestone.id)
    return milestone


@router.get("/milestones", response_model=MilestoneListResponse)
async def list_milestones(
    project_id: int = Query(..., description="Filter by project"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List milestones for a project"""
    query = select(Milestone).where(Milestone.project_id == project_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(Milestone.due_date.asc().nullsfirst(), Milestone.created_at.desc())
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    milestones = result.scalars().all()

    return MilestoneListResponse(milestones=milestones, total=total)


@router.put("/milestones/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    milestone_id: int,
    milestone_data: MilestoneUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a milestone"""
    result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    update_data = milestone_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(milestone, field, value)

    await db.commit()
    await db.refresh(milestone)

    logger.info("Milestone updated", user_id=current_user.id, milestone_id=milestone_id)
    return milestone


# =====================================================
# TEST RUNS
# =====================================================

@router.post("/test-runs", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def create_test_run(
    run_data: TestRunCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new test run with selected test cases"""
    logger.info("Creating test run", user_id=current_user.id, name=run_data.name)

    # Verify project exists and belongs to user
    project_result = await db.execute(
        select(Project).where(
            and_(
                Project.id == run_data.project_id,
                Project.created_by_id == current_user.id
            )
        )
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify milestone if provided
    if run_data.milestone_id:
        milestone_result = await db.execute(
            select(Milestone).where(
                and_(
                    Milestone.id == run_data.milestone_id,
                    Milestone.project_id == run_data.project_id
                )
            )
        )
        milestone = milestone_result.scalar_one_or_none()
        if not milestone:
            raise HTTPException(status_code=404, detail="Milestone not found in this project")

    # Determine which test cases to include
    included_case_ids = []
    if run_data.include_all:
        # Get all test cases from the project
        cases_query = select(RepositoryTestCase).where(
            RepositoryTestCase.suite_id.in_(
                select(TestSuite.id).where(TestSuite.project_id == run_data.project_id)
            )
        )
        cases_result = await db.execute(cases_query)
        cases = cases_result.scalars().all()
        included_case_ids = [c.id for c in cases]
    elif run_data.included_case_ids:
        included_case_ids = run_data.included_case_ids

    logger.info("Test cases to include", count=len(included_case_ids))

    try:
        test_run = TestRun(
            name=run_data.name,
            description=run_data.description,
            project_id=run_data.project_id,
            milestone_id=run_data.milestone_id,
            include_all=run_data.include_all,
            included_case_ids=included_case_ids,
            created_by_id=current_user.id
        )

        db.add(test_run)
        await db.flush()  # Get the ID

        # Create test results for each included test case
        for case_id in included_case_ids:
            result = TestResult(
                test_run_id=test_run.id,
                test_case_id=case_id,
                status=TestResultStatus.PENDING
            )
            db.add(result)

        await db.commit()
        await db.refresh(test_run)
    except Exception as e:
        logger.error("Error creating test run", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create test run: {str(e)}")

    logger.info(
        "Test run created",
        user_id=current_user.id,
        test_run_id=test_run.id,
        case_count=len(included_case_ids)
    )

    # Reload with test_results to calculate progress
    result = await db.execute(
        select(TestRun)
        .options(selectinload(TestRun.test_results))
        .where(TestRun.id == test_run.id)
    )
    test_run = result.scalar_one_or_none()

    # Build response with progress
    total = len(test_run.test_results) if test_run.test_results else 0
    return TestRunResponse(
        id=test_run.id,
        name=test_run.name,
        description=test_run.description,
        project_id=test_run.project_id,
        milestone_id=test_run.milestone_id,
        status=test_run.status,
        include_all=test_run.include_all,
        included_case_ids=test_run.included_case_ids,
        created_at=test_run.created_at,
        updated_at=test_run.updated_at,
        created_by_id=test_run.created_by_id,
        completed_at=test_run.completed_at,
        progress={
            "total": total,
            "passed": 0,
            "failed": 0,
            "blocked": 0,
            "skipped": 0,
            "pending": total,
            "pass_rate": 0
        }
    )


@router.get("/test-runs", response_model=TestRunListResponse)
async def list_test_runs(
    project_id: int = Query(..., description="Filter by project"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[TestRunStatus] = Query(None, description="Filter by status"),
    milestone_id: Optional[int] = Query(None, description="Filter by milestone"),
):
    """List test runs"""
    query = select(TestRun).where(TestRun.project_id == project_id)

    if status:
        query = query.where(TestRun.status == status)
    if milestone_id:
        query = query.where(TestRun.milestone_id == milestone_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results with eager load of results count
    query = query.order_by(TestRun.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    test_runs = result.scalars().all()

    # Enrich with progress
    run_responses = []
    for run in test_runs:
        # Get progress
        progress_result = await db.execute(
            select(TestResult).where(TestResult.test_run_id == run.id)
        )
        results = progress_result.scalars().all()

        # Calculate progress
        total = len(results)
        passed = sum(1 for r in results if r.status == TestResultStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestResultStatus.FAILED)
        blocked = sum(1 for r in results if r.status == TestResultStatus.BLOCKED)
        skipped = sum(1 for r in results if r.status == TestResultStatus.SKIPPED)
        pending = sum(1 for r in results if r.status == TestResultStatus.PENDING)
        retest = sum(1 for r in results if r.status == TestResultStatus.RETEST)

        pass_rate = (passed / total * 100) if total > 0 else 0

        run_responses.append(TestRunResponse(
            id=run.id,
            name=run.name,
            description=run.description,
            project_id=run.project_id,
            milestone_id=run.milestone_id,
            status=run.status,
            include_all=run.include_all,
            included_case_ids=run.included_case_ids,
            created_at=run.created_at,
            updated_at=run.updated_at,
            created_by_id=run.created_by_id,
            completed_at=run.completed_at,
            progress={
                "total": total,
                "passed": passed,
                "failed": failed,
                "blocked": blocked,
                "skipped": skipped,
                "pending": pending + retest,
                "pass_rate": round(pass_rate, 1)
            }
        ))

    return TestRunListResponse(test_runs=run_responses, total=total)


@router.get("/test-runs/{test_run_id}", response_model=TestRunWithResultsResponse)
async def get_test_run(
    test_run_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get test run with all test results"""
    try:
        result = await db.execute(
            select(TestRun)
            .options(selectinload(TestRun.test_results).selectinload(TestResult.test_case))
            .where(TestRun.id == test_run_id)
        )
        test_run = result.scalar_one_or_none()

        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")

        # Build response with results
        test_results = []
        for r in test_run.test_results:
            # Convert evidence dict to EvidenceItem objects if present
            evidence_list = None
            if r.evidence:
                evidence_list = [EvidenceItem(**e) for e in r.evidence]

            test_results.append(TestResultResponse(
                id=r.id,
                test_run_id=r.test_run_id,
                test_case_id=r.test_case_id,
                status=r.status,
                assigned_to_id=r.assigned_to_id,
                actual_result=r.actual_result,
                comments=r.comments,
                defects=r.defects,
                execution_seconds=r.execution_seconds,
                executed_at=r.executed_at,
                executed_by_id=r.executed_by_id,
                created_at=r.created_at,
                updated_at=r.updated_at,
                evidence=evidence_list,
                test_case=RepositoryTestCaseResponse.model_validate(r.test_case) if r.test_case else None
            ))

        # Calculate progress
        total = len(test_run.test_results)
        passed = sum(1 for r in test_run.test_results if r.status == TestResultStatus.PASSED)

        return TestRunWithResultsResponse(
            id=test_run.id,
            name=test_run.name,
            description=test_run.description,
            project_id=test_run.project_id,
            milestone_id=test_run.milestone_id,
            status=test_run.status,
            include_all=test_run.include_all,
            included_case_ids=test_run.included_case_ids,
            created_at=test_run.created_at,
            updated_at=test_run.updated_at,
            created_by_id=test_run.created_by_id,
            completed_at=test_run.completed_at,
            progress={"total": total, "passed": passed, "failed": total - passed},
            test_results=test_results
        )
    except Exception as e:
        logger.error("Error getting test run", error=str(e), test_run_id=test_run_id)
        raise HTTPException(status_code=500, detail=f"Failed to get test run: {str(e)}")


@router.put("/test-runs/{test_run_id}", response_model=TestRunResponse)
async def update_test_run(
    test_run_id: int,
    run_data: TestRunUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update test run (status, name, etc.)"""
    result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
    test_run = result.scalar_one_or_none()

    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    # Check for pending results before allowing completion
    if run_data.status == TestRunStatus.COMPLETED:
        progress_result = await db.execute(
            select(TestResult).where(TestResult.test_run_id == test_run.id)
        )
        results = progress_result.scalars().all()
        pending_count = sum(1 for r in results if r.status in (TestResultStatus.PENDING, TestResultStatus.RETEST))

        if pending_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot complete test run with {pending_count} pending test(s). Please update all test results first."
            )

    update_data = run_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(test_run, field, value)

    # If marking as completed, set completed_at
    if run_data.status == TestRunStatus.COMPLETED and not test_run.completed_at:
        test_run.completed_at = datetime.utcnow()
        test_run.completed_by_id = current_user.id

    await db.commit()
    await db.refresh(test_run)

    # Calculate progress for response
    progress_result = await db.execute(
        select(TestResult).where(TestResult.test_run_id == test_run.id)
    )
    results = progress_result.scalars().all()

    total = len(results)
    passed = sum(1 for r in results if r.status == TestResultStatus.PASSED)
    failed = sum(1 for r in results if r.status == TestResultStatus.FAILED)
    blocked = sum(1 for r in results if r.status == TestResultStatus.BLOCKED)
    skipped = sum(1 for r in results if r.status == TestResultStatus.SKIPPED)
    pending = sum(1 for r in results if r.status == TestResultStatus.PENDING)
    retest = sum(1 for r in results if r.status == TestResultStatus.RETEST)

    pass_rate = (passed / total * 100) if total > 0 else 0

    logger.info("Test run updated", user_id=current_user.id, test_run_id=test_run_id)
    return TestRunResponse(
        id=test_run.id,
        name=test_run.name,
        description=test_run.description,
        project_id=test_run.project_id,
        milestone_id=test_run.milestone_id,
        status=test_run.status,
        include_all=test_run.include_all,
        included_case_ids=test_run.included_case_ids,
        created_at=test_run.created_at,
        updated_at=test_run.updated_at,
        created_by_id=test_run.created_by_id,
        completed_at=test_run.completed_at,
        progress={
            "total": total,
            "passed": passed,
            "failed": failed,
            "blocked": blocked,
            "skipped": skipped,
            "pending": pending + retest,
            "pass_rate": round(pass_rate, 1)
        }
    )


@router.delete("/test-runs/{test_run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_run(
    test_run_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a test run (cascade deletes all results)"""
    result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
    test_run = result.scalar_one_or_none()

    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    await db.delete(test_run)
    await db.commit()

    logger.info("Test run deleted", user_id=current_user.id, test_run_id=test_run_id)
    return None


@router.post("/test-runs/{test_run_id}/cancel", response_model=TestRunResponse)
async def cancel_test_run(
    test_run_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a test run (only if status is planned or in_progress)"""
    result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
    test_run = result.scalar_one_or_none()

    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    if test_run.status not in [TestRunStatus.PLANNED, TestRunStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel test run with status {test_run.status.value}"
        )

    test_run.status = TestRunStatus.CANCELLED
    await db.commit()
    await db.refresh(test_run)

    logger.info("Test run cancelled", user_id=current_user.id, test_run_id=test_run_id)

    # Build response manually
    return TestRunResponse(
        id=test_run.id,
        name=test_run.name,
        description=test_run.description,
        status=test_run.status,
        project_id=test_run.project_id,
        milestone_id=test_run.milestone_id,
        created_by_id=test_run.created_by_id,
        completed_by_id=test_run.completed_by_id,
        completed_at=test_run.completed_at,
        created_at=test_run.created_at,
        updated_at=test_run.updated_at,
        progress={
            "total": 0,
            "passed": 0,
            "failed": 0,
            "blocked": 0,
            "skipped": 0,
            "pending": 0,
            "pass_rate": 0
        }
    )


# =====================================================
# TEST RESULTS
# =====================================================

@router.put("/test-results/{result_id}", response_model=TestResultResponse)
async def update_test_result(
    result_id: int,
    result_data: TestResultUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a single test result"""
    result = await db.execute(
        select(TestResult)
        .options(selectinload(TestResult.test_case))
        .where(TestResult.id == result_id)
    )
    test_result = result.scalar_one_or_none()

    if not test_result:
        raise HTTPException(status_code=404, detail="Test result not found")

    update_data = result_data.model_dump(exclude_unset=True)

    # If status is changing from pending, record execution time
    if "status" in update_data and update_data["status"] != TestResultStatus.PENDING:
        if test_result.status == TestResultStatus.PENDING:
            test_result.executed_at = datetime.utcnow()
            test_result.executed_by_id = current_user.id

    for field, value in update_data.items():
        setattr(test_result, field, value)

    await db.commit()
    await db.refresh(test_result)

    # Convert evidence dict to EvidenceItem objects if present
    evidence_list = None
    if test_result.evidence:
        evidence_list = [EvidenceItem(**e) for e in test_result.evidence]

    # Build response
    response = TestResultResponse(
        id=test_result.id,
        test_run_id=test_result.test_run_id,
        test_case_id=test_result.test_case_id,
        status=test_result.status,
        assigned_to_id=test_result.assigned_to_id,
        actual_result=test_result.actual_result,
        comments=test_result.comments,
        defects=test_result.defects,
        execution_seconds=test_result.execution_seconds,
        executed_at=test_result.executed_at,
        executed_by_id=test_result.executed_by_id,
        created_at=test_result.created_at,
        updated_at=test_result.updated_at,
        evidence=evidence_list,
        test_case=RepositoryTestCaseResponse.model_validate(test_result.test_case) if test_result.test_case else None
    )

    logger.info("Test result updated", user_id=current_user.id, result_id=result_id)
    return response


@router.put("/test-results/bulk", response_model=BulkResultUpdateResponse)
async def bulk_update_test_results(
    bulk_data: BulkResultUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update multiple test results at once"""
    logger.info("Bulk updating test results", user_id=current_user.id, count=len(bulk_data.result_ids))

    updated_ids = []
    update_dict = bulk_data.model_dump(exclude_unset=True, exclude={"result_ids"})

    for result_id in bulk_data.result_ids:
        result = await db.execute(
            select(TestResult).where(TestResult.id == result_id)
        )
        test_result = result.scalar_one_or_none()

        if test_result:
            # If status is changing from pending, record execution time
            if "status" in update_dict and update_dict["status"] != TestResultStatus.PENDING:
                if test_result.status == TestResultStatus.PENDING:
                    test_result.executed_at = datetime.utcnow()
                    test_result.executed_by_id = current_user.id

            for field, value in update_dict.items():
                setattr(test_result, field, value)

            updated_ids.append(result_id)

    await db.commit()

    logger.info("Bulk update completed", user_id=current_user.id, updated_count=len(updated_ids))
    return BulkResultUpdateResponse(updated_count=len(updated_ids), updated_ids=updated_ids)


# =====================================================
# EVIDENCE UPLOAD
# =====================================================

def _get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _is_allowed_file(filename: str) -> tuple[bool, str | None]:
    """Check if file type is allowed and return (is_allowed, type)"""
    ext = _get_file_extension(filename)
    if ext in settings.ALLOWED_IMAGE_TYPES:
        return True, "image"
    elif ext in settings.ALLOWED_VIDEO_TYPES:
        return True, "video"
    return False, None


async def _compress_image(content: bytes, original_filename: str, max_size_mb: int = 2) -> Tuple[bytes, str]:
    """
    Compress image to reduce file size.
    Returns (compressed_content, original_ext)
    """
    if not PILLOW_AVAILABLE:
        return content, _get_file_extension(original_filename)

    try:
        img = Image.open(BytesIO(content))

        # Convert RGBA to RGB for JPEG compatibility
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background for transparent images
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        # Resize if image is too large (max dimension 1920px)
        max_dimension = 1920
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.LANCZOS)

        # Try to compress with different quality levels
        output = BytesIO()
        original_ext = _get_file_extension(original_filename)

        # Use JPEG for better compression, fall back to original format
        save_format = 'JPEG' if original_ext.lower() in ('jpg', 'jpeg', 'png', 'webp') else original_ext.upper()
        if save_format == 'JPEG':
            # Progressive JPEG for better loading
            img.save(output, format='JPEG', quality=85, optimize=True, progressive=True)
        elif save_format == 'PNG':
            img.save(output, format='PNG', optimize=True)
        elif save_format == 'WEBP':
            img.save(output, format='WEBP', quality=85, method=6)
        else:
            # Fallback - save as-is
            return content, original_ext

        compressed_content = output.getvalue()

        # Check if compression actually helped
        if len(compressed_content) >= len(content):
            return content, original_ext

        # Update extension if we converted to JPEG
        if save_format == 'JPEG' and original_ext.lower() not in ('jpg', 'jpeg'):
            return compressed_content, 'jpg'

        return compressed_content, original_ext

    except Exception as e:
        logger.warning(f"Image compression failed: {e}, using original")
        return content, _get_file_extension(original_filename)


@router.post("/test-results/{result_id}/evidence", response_model=EvidenceItem, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    result_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload evidence (image or video) for a test result"""
    logger.info("Uploading evidence", user_id=current_user.id, result_id=result_id, filename=file.filename)

    # Verify test result exists
    result = await db.execute(select(TestResult).where(TestResult.id == result_id))
    test_result = result.scalar_one_or_none()
    if not test_result:
        raise HTTPException(status_code=404, detail="Test result not found")

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    is_allowed, file_type = _is_allowed_file(file.filename)
    if not is_allowed:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {settings.ALLOWED_IMAGE_TYPES + settings.ALLOWED_VIDEO_TYPES}"
        )

    # Check file size
    content = await file.read()
    file_size = len(content)
    max_size = settings.MAX_EVIDENCE_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_EVIDENCE_SIZE_MB}MB"
        )

    # Compress images if available
    if file_type == "image":
        content, ext = await _compress_image(content, file.filename)
        file_size = len(content)

    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.EVIDENCE_UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    unique_id = str(uuid.uuid4())
    new_filename = f"{unique_id}.{ext}"
    file_path = upload_dir / new_filename

    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create evidence metadata
    evidence_item = EvidenceItem(
        id=unique_id,
        type=file_type,
        url=f"/v1/test-repository/evidence/{unique_id}",
        filename=file.filename,
        size_bytes=file_size,
        uploaded_at=datetime.utcnow().isoformat()
    )

    # Add to test result's evidence list
    # Store actual file extension separately for retrieval (since format may change during compression)
    if test_result.evidence is None:
        test_result.evidence = []
    evidence_dict = evidence_item.model_dump(mode='json')
    evidence_dict['file_extension'] = ext  # Store actual file extension used
    test_result.evidence.append(evidence_dict)

    await db.commit()

    logger.info("Evidence uploaded successfully", user_id=current_user.id, result_id=result_id, evidence_id=unique_id)
    return evidence_item


@router.delete("/test-results/{result_id}/evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    result_id: int,
    evidence_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete evidence from a test result"""
    logger.info("Deleting evidence", user_id=current_user.id, result_id=result_id, evidence_id=evidence_id)

    # Verify test result exists
    result = await db.execute(select(TestResult).where(TestResult.id == result_id))
    test_result = result.scalar_one_or_none()
    if not test_result:
        raise HTTPException(status_code=404, detail="Test result not found")

    # Find and remove the evidence
    if not test_result.evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    evidence_to_delete = None
    for evidence in test_result.evidence:
        if evidence.get("id") == evidence_id:
            evidence_to_delete = evidence
            break

    if not evidence_to_delete:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # Delete physical file
    ext = evidence_to_delete.get("file_extension") or _get_file_extension(evidence_to_delete.get('filename', ''))
    file_path = Path(settings.EVIDENCE_UPLOAD_DIR) / f"{evidence_id}.{ext}"
    if file_path.exists():
        file_path.unlink()

    # Remove from evidence list
    test_result.evidence = [e for e in test_result.evidence if e.get("id") != evidence_id]

    await db.commit()

    logger.info("Evidence deleted successfully", user_id=current_user.id, result_id=result_id, evidence_id=evidence_id)
    return None


@router.get("/evidence/{evidence_id}")
async def get_evidence(
    evidence_id: str,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get evidence file by ID. Requires token query parameter for authentication when loading from img tags."""
    # Authenticate via token parameter (for img tags) or skip for public access with unguessable IDs
    current_user = None
    if token:
        try:
            from app.core.security import verify_token as verify_jwt_token
            payload = verify_jwt_token(token)
            # Get user from database
            user_result = await db.execute(select(User).where(User.id == int(payload.get("sub", 0))))
            current_user = user_result.scalar_one_or_none()
        except:
            pass  # Allow access with unguessable UUID even without valid token

    # Find the evidence in any test result
    result = await db.execute(
        select(TestResult).where(TestResult.evidence.is_not(None))
    )
    test_results = result.scalars().all()

    evidence_data = None
    for test_result in test_results:
        if test_result.evidence:
            for evidence in test_result.evidence:
                if evidence.get("id") == evidence_id:
                    evidence_data = evidence
                    break
        if evidence_data:
            break

    if not evidence_data:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # Get file extension from stored data (may differ from original filename due to compression)
    ext = evidence_data.get("file_extension") or _get_file_extension(evidence_data.get("filename", ""))
    file_path = Path(settings.EVIDENCE_UPLOAD_DIR) / f"{evidence_id}.{ext}"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine media type
    media_type_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "mp4": "video/mp4",
        "webm": "video/webm",
        "mov": "video/quicktime",
        "avi": "video/x-msvideo",
    }
    media_type = media_type_map.get(ext, "application/octet-stream")

    # Return file
    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=evidence_data.get("filename", f"evidence.{ext}")
    )
