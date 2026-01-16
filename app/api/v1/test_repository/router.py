"""Test Management / Repository API Router

Endpoints for managing Projects, Test Suites, and Test Cases
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete, null
from typing import Optional, List
from datetime import datetime
import json

from app.db.session import get_db
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from app.models.test_repository import Project, TestSuite, RepositoryTestCase, Priority, AutomationStatus, RepositoryTestCaseType, TestCaseVersion
from app.schemas.test_repository_schema import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    TestSuiteCreate,
    TestSuiteUpdate,
    TestSuiteResponse,
    TestSuiteTree,
    TestSuiteListResponse,
    RepositoryTestCaseCreate,
    RepositoryTestCaseUpdate,
    RepositoryTestCaseResponse,
    RepositoryTestCaseListResponse,
    BulkUpdateRequest,
    BulkUpdateResponse,
    BulkDeleteResponse,
    ImportTestCaseRequest,
    ImportResponse,
    ExportRequest,
    SaveToRepositoryRequest,
    SaveToRepositoryResponse,
    TestCaseType,
    TestCaseVersionResponse,
    TestCaseVersionListResponse,
    RestoreVersionRequest,
)
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


# =====================================================
# PROJECTS
# =====================================================

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    logger.info("Creating project", user_id=current_user.id, name=project_data.name)

    project = Project(
        name=project_data.name,
        description=project_data.description,
        created_by_id=current_user.id,
        is_active=True
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    logger.info("Project created", user_id=current_user.id, project_id=project.id)
    return project


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search in name or description"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """List all projects"""
    logger.info("Listing projects", user_id=current_user.id, skip=skip, limit=limit)

    # Build query
    query = select(Project)

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Project.name.ilike(search_pattern),
                Project.description.ilike(search_pattern)
            )
        )

    if is_active is not None:
        query = query.where(Project.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(Project.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()

    # Enrich with counts
    project_responses = []
    for project in projects:
        # Count suites
        suite_count_result = await db.execute(
            select(func.count()).select_from(select(TestSuite).where(TestSuite.project_id == project.id).subquery())
        )
        suite_count = suite_count_result.scalar() or 0

        # Count test cases (recursively through all suites)
        case_count_result = await db.execute(
            select(func.count()).select_from(
                select(RepositoryTestCase).where(
                    RepositoryTestCase.suite_id.in_(
                        select(TestSuite.id).where(TestSuite.project_id == project.id)
                    )
                ).subquery()
            )
        )
        case_count = case_count_result.scalar() or 0

        project_responses.append(ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            is_active=project.is_active,
            created_at=project.created_at,
            updated_at=project.updated_at,
            created_by_id=project.created_by_id,
            suite_count=suite_count,
            case_count=case_count
        ))

    return ProjectListResponse(projects=project_responses, total=total)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific project by ID"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Count suites
    suite_count_result = await db.execute(
        select(func.count()).select_from(select(TestSuite).where(TestSuite.project_id == project.id).subquery())
    )
    suite_count = suite_count_result.scalar() or 0

    # Count test cases
    case_count_result = await db.execute(
        select(func.count()).select_from(
            select(RepositoryTestCase).where(
                RepositoryTestCase.suite_id.in_(
                    select(TestSuite.id).where(TestSuite.project_id == project.id)
                )
            ).subquery()
        )
    )
    case_count = case_count_result.scalar() or 0

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        is_active=project.is_active,
        created_at=project.created_at,
        updated_at=project.updated_at,
        created_by_id=project.created_by_id,
        suite_count=suite_count,
        case_count=case_count
    )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update fields
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    logger.info("Project updated", user_id=current_user.id, project_id=project.id)
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a project (cascade deletes all suites and test cases)"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()

    logger.info("Project deleted", user_id=current_user.id, project_id=project_id)
    return None


# =====================================================
# TEST SUITES
# =====================================================

@router.post("/suites", response_model=TestSuiteResponse, status_code=status.HTTP_201_CREATED)
async def create_suite(
    suite_data: TestSuiteCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new test suite"""
    logger.info("Creating test suite", user_id=current_user.id, name=suite_data.name)

    # Verify project exists
    project_result = await db.execute(select(Project).where(Project.id == suite_data.project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # If parent_id specified, verify it exists
    if suite_data.parent_id:
        parent_result = await db.execute(select(TestSuite).where(TestSuite.id == suite_data.parent_id))
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent suite not found")

    # Get next position
    position_result = await db.execute(
        select(func.count()).select_from(
            select(TestSuite).where(
                TestSuite.project_id == suite_data.project_id,
                TestSuite.parent_id == suite_data.parent_id
            ).subquery()
        )
    )
    position = position_result.scalar() or 0

    suite = TestSuite(
        name=suite_data.name,
        description=suite_data.description,
        project_id=suite_data.project_id,
        parent_id=suite_data.parent_id,
        position=position,
        created_by_id=current_user.id
    )

    db.add(suite)
    await db.commit()
    await db.refresh(suite)

    logger.info("Test suite created", user_id=current_user.id, suite_id=suite.id)

    # Build response manually to avoid lazy loading issues with case_count
    return TestSuiteResponse(
        id=suite.id,
        name=suite.name,
        description=suite.description,
        project_id=suite.project_id,
        parent_id=suite.parent_id,
        position=suite.position,
        created_at=suite.created_at,
        updated_at=suite.updated_at,
        created_by_id=suite.created_by_id,
        case_count=0  # New suite has no cases
    )


@router.get("/suites", response_model=TestSuiteListResponse)
async def list_suites(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    project_id: Optional[int] = Query(None, description="Filter by project"),
    parent_id: Optional[int] = Query(None, description="Filter by parent suite (null for root)"),
    include_nested: bool = Query(False, description="Include nested suites"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """List test suites"""
    logger.info("Listing test suites", user_id=current_user.id, project_id=project_id)

    # Build query
    query = select(TestSuite)

    # Apply filters
    if project_id is not None:
        query = query.where(TestSuite.project_id == project_id)

    if parent_id is not None:
        query = query.where(TestSuite.parent_id == parent_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(TestSuite.position, TestSuite.name).offset(skip).limit(limit)
    result = await db.execute(query)
    suites = result.scalars().all()

    # Enrich with case counts
    suite_responses = []
    for suite in suites:
        case_count_result = await db.execute(
            select(func.count()).select_from(
                select(RepositoryTestCase).where(RepositoryTestCase.suite_id == suite.id).subquery()
            )
        )
        case_count = case_count_result.scalar() or 0

        suite_responses.append(TestSuiteResponse(
            id=suite.id,
            name=suite.name,
            description=suite.description,
            project_id=suite.project_id,
            parent_id=suite.parent_id,
            position=suite.position,
            created_at=suite.created_at,
            updated_at=suite.updated_at,
            created_by_id=suite.created_by_id,
            case_count=case_count
        ))

    return TestSuiteListResponse(suites=suite_responses, total=total)


@router.get("/suites/{suite_id}", response_model=TestSuiteResponse)
async def get_suite(
    suite_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific test suite"""
    result = await db.execute(select(TestSuite).where(TestSuite.id == suite_id))
    suite = result.scalar_one_or_none()

    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    case_count_result = await db.execute(
        select(func.count()).select_from(
            select(RepositoryTestCase).where(RepositoryTestCase.suite_id == suite.id).subquery()
        )
    )
    case_count = case_count_result.scalar() or 0

    return TestSuiteResponse(
        id=suite.id,
        name=suite.name,
        description=suite.description,
        project_id=suite.project_id,
        parent_id=suite.parent_id,
        position=suite.position,
        created_at=suite.created_at,
        updated_at=suite.updated_at,
        created_by_id=suite.created_by_id,
        case_count=case_count
    )


@router.get("/suites/{suite_id}/tree", response_model=List[TestSuiteTree])
async def get_suite_tree(
    suite_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get suite tree with nested children and test cases"""
    # If suite_id provided, start from that suite, otherwise get root suites
    if suite_id:
        result = await db.execute(select(TestSuite).where(TestSuite.id == suite_id))
        suite = result.scalar_one_or_none()
        if not suite:
            raise HTTPException(status_code=404, detail="Test suite not found")
        suites = [suite]
    else:
        # Get root suites (no parent)
        result = await db.execute(select(TestSuite).where(TestSuite.parent_id.is_(null())).order_by(TestSuite.position))
        suites = result.scalars().all()

    async def build_tree(suite: TestSuite) -> TestSuiteTree:
        # Get test cases for this suite
        tc_result = await db.execute(
            select(RepositoryTestCase).where(RepositoryTestCase.suite_id == suite.id).order_by(RepositoryTestCase.position)
        )
        test_cases = tc_result.scalars().all()

        # Get child suites
        children_result = await db.execute(
            select(TestSuite).where(TestSuite.parent_id == suite.id).order_by(TestSuite.position)
        )
        children = await children_result.scalars().all()

        # Build tree recursively
        return TestSuiteTree(
            id=suite.id,
            name=suite.name,
            description=suite.description,
            project_id=suite.project_id,
            parent_id=suite.parent_id,
            position=suite.position,
            created_at=suite.created_at,
            updated_at=suite.updated_at,
            created_by_id=suite.created_by_id,
            case_count=len(test_cases),
            children=[await build_tree(child) for child in children],
            test_cases=test_cases
        )

    tree = [await build_tree(suite) for suite in suites]
    return tree


@router.put("/suites/{suite_id}", response_model=TestSuiteResponse)
async def update_suite(
    suite_id: int,
    suite_data: TestSuiteUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a test suite"""
    result = await db.execute(select(TestSuite).where(TestSuite.id == suite_id))
    suite = result.scalar_one_or_none()

    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    # Update fields
    update_data = suite_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(suite, field, value)

    await db.commit()
    await db.refresh(suite)

    logger.info("Test suite updated", user_id=current_user.id, suite_id=suite.id)

    # Get case count
    case_count_result = await db.execute(
        select(func.count()).select_from(
            select(RepositoryTestCase).where(RepositoryTestCase.suite_id == suite_id).subquery()
        )
    )
    case_count = case_count_result.scalar() or 0

    # Build response manually to avoid lazy loading issues
    return TestSuiteResponse(
        id=suite.id,
        name=suite.name,
        description=suite.description,
        project_id=suite.project_id,
        parent_id=suite.parent_id,
        position=suite.position,
        created_at=suite.created_at,
        updated_at=suite.updated_at,
        created_by_id=suite.created_by_id,
        case_count=case_count
    )


@router.delete("/suites/{suite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_suite(
    suite_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a test suite (cascade deletes all test cases)"""
    result = await db.execute(select(TestSuite).where(TestSuite.id == suite_id))
    suite = result.scalar_one_or_none()

    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    try:
        await db.delete(suite)
        await db.commit()
    except Exception as e:
        await db.rollback()
        # Check for foreign key constraint violations
        if "foreign key constraint" in str(e).lower() or "fk_test_results_test_case" in str(e):
            raise HTTPException(
                status_code=400,
                detail="Cannot delete suite: test cases in this suite are used in test runs. Please delete the related test runs first."
            )
        raise e

    logger.info("Test suite deleted", user_id=current_user.id, suite_id=suite_id)
    return None


# =====================================================
# REPOSITORY TEST CASES
# =====================================================

@router.post("/test-cases", response_model=RepositoryTestCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    test_case_data: RepositoryTestCaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new test case"""
    logger.info("Creating test case", user_id=current_user.id, title=test_case_data.title)

    # Verify suite exists
    suite_result = await db.execute(select(TestSuite).where(TestSuite.id == test_case_data.suite_id))
    suite = suite_result.scalar_one_or_none()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    # Get next position
    position_result = await db.execute(
        select(func.count()).select_from(
            select(RepositoryTestCase).where(RepositoryTestCase.suite_id == test_case_data.suite_id).subquery()
        )
    )
    position = position_result.scalar() or 0

    test_case = RepositoryTestCase(
        suite_id=test_case_data.suite_id,
        external_id=test_case_data.external_id,
        title=test_case_data.title,
        description=test_case_data.description,
        tc_type=test_case_data.tc_type,
        priority=test_case_data.priority,
        automation_status=test_case_data.automation_status,
        estimated_minutes=test_case_data.estimated_minutes,
        preconditions=test_case_data.preconditions,
        steps=[step.model_dump() for step in (test_case_data.steps or [])],
        expected_result=test_case_data.expected_result,
        tags=test_case_data.tags,
        custom_fields=test_case_data.custom_fields,
        position=position,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(test_case)
    await db.commit()
    await db.refresh(test_case)

    logger.info("Test case created", user_id=current_user.id, test_case_id=test_case.id)
    return test_case


@router.get("/test-cases", response_model=RepositoryTestCaseListResponse)
async def list_test_cases(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    project_id: Optional[int] = Query(None, description="Filter by project"),
    suite_id: Optional[int] = Query(None, description="Filter by suite"),
    tc_type: Optional[TestCaseType] = Query(None, description="Filter by type"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    automation_status: Optional[AutomationStatus] = Query(None, description="Filter by automation status"),
    is_draft: Optional[bool] = Query(None, description="Filter by draft status"),
    search: Optional[str] = Query(None, description="Search in title or description"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List test cases with filters and pagination"""
    skip = (page - 1) * page_size

    # Build query
    query = select(RepositoryTestCase)

    # Apply filters
    if suite_id is not None:
        query = query.where(RepositoryTestCase.suite_id == suite_id)
    elif project_id is not None:
        # Filter by all suites in project
        query = query.where(
            RepositoryTestCase.suite_id.in_(
                select(TestSuite.id).where(TestSuite.project_id == project_id)
            )
        )

    if tc_type is not None:
        query = query.where(RepositoryTestCase.tc_type == tc_type)

    if priority is not None:
        query = query.where(RepositoryTestCase.priority == priority)

    if automation_status is not None:
        query = query.where(RepositoryTestCase.automation_status == automation_status)

    if is_draft is not None:
        query = query.where(RepositoryTestCase.is_draft == is_draft)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                RepositoryTestCase.title.ilike(search_pattern),
                RepositoryTestCase.description.ilike(search_pattern)
            )
        )

    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag in tag_list:
            query = query.where(RepositoryTestCase.tags.contains([tag]))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(RepositoryTestCase.position, RepositoryTestCase.title).offset(skip).limit(page_size)
    result = await db.execute(query)
    test_cases = result.scalars().all()

    return RepositoryTestCaseListResponse(
        test_cases=test_cases,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/test-cases/{test_case_id}", response_model=RepositoryTestCaseResponse)
async def get_test_case(
    test_case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific test case by ID"""
    result = await db.execute(select(RepositoryTestCase).where(RepositoryTestCase.id == test_case_id))
    test_case = result.scalar_one_or_none()

    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    return test_case


@router.put("/test-cases/{test_case_id}", response_model=RepositoryTestCaseResponse)
async def update_test_case(
    test_case_id: int,
    test_case_data: RepositoryTestCaseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a test case"""
    result = await db.execute(select(RepositoryTestCase).where(RepositoryTestCase.id == test_case_id))
    test_case = result.scalar_one_or_none()

    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    # Create a version snapshot before updating
    version_snapshot = TestCaseVersion(
        test_case_id=test_case_id,
        version=test_case.version,
        title=test_case.title,
        description=test_case.description,
        tc_type=test_case.tc_type,
        priority=test_case.priority,
        automation_status=test_case.automation_status,
        estimated_minutes=test_case.estimated_minutes,
        preconditions=test_case.preconditions,
        steps=test_case.steps,
        expected_result=test_case.expected_result,
        tags=test_case.tags,
        custom_fields=test_case.custom_fields,
        change_summary=test_case_data.change_summary,
        changed_by_id=current_user.id,
    )
    db.add(version_snapshot)

    # Update fields
    update_data = test_case_data.model_dump(exclude_unset=True, exclude={"change_summary"})

    # Handle steps separately to convert to dict
    if "steps" in update_data and update_data["steps"] is not None:
        update_data["steps"] = [step.model_dump() for step in update_data["steps"]]

    for field, value in update_data.items():
        setattr(test_case, field, value)

    # Update tracking
    test_case.updated_by_id = current_user.id
    test_case.version += 1

    await db.commit()
    await db.refresh(test_case)

    logger.info("Test case updated", user_id=current_user.id, test_case_id=test_case_id, new_version=test_case.version)
    return RepositoryTestCaseResponse.model_validate(test_case)


@router.delete("/test-cases/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(
    test_case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a test case"""
    result = await db.execute(select(RepositoryTestCase).where(RepositoryTestCase.id == test_case_id))
    test_case = result.scalar_one_or_none()

    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    await db.delete(test_case)
    await db.commit()

    logger.info("Test case deleted", user_id=current_user.id, test_case_id=test_case_id)
    return None


# =====================================================
# BULK OPERATIONS
# =====================================================

@router.put("/test-cases/bulk", response_model=BulkUpdateResponse)
async def bulk_update_test_cases(
    bulk_data: BulkUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update multiple test cases at once"""
    logger.info("Bulk updating test cases", user_id=current_user.id, count=len(bulk_data.test_case_ids))

    updated_ids = []
    update_dict = bulk_data.updates.model_dump(exclude_unset=True, exclude_none=True)

    # Handle steps separately
    if "steps" in update_dict and update_dict["steps"] is not None:
        update_dict["steps"] = [step.model_dump() for step in bulk_data.updates.steps]

    for test_case_id in bulk_data.test_case_ids:
        result = await db.execute(select(RepositoryTestCase).where(RepositoryTestCase.id == test_case_id))
        test_case = result.scalar_one_or_none()

        if test_case:
            for field, value in update_dict.items():
                setattr(test_case, field, value)

            test_case.updated_by_id = current_user.id
            test_case.version += 1
            updated_ids.append(test_case_id)

    await db.commit()

    logger.info("Bulk update completed", user_id=current_user.id, updated_count=len(updated_ids))
    return BulkUpdateResponse(updated_count=len(updated_ids), updated_ids=updated_ids)


@router.delete("/test-cases/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_test_cases(
    test_case_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete multiple test cases at once"""
    logger.info("Bulk deleting test cases", user_id=current_user.id, count=len(test_case_ids))

    await db.execute(
        delete(RepositoryTestCase).where(RepositoryTestCase.id.in_(test_case_ids))
    )
    await db.commit()

    logger.info("Bulk delete completed", user_id=current_user.id, deleted_count=len(test_case_ids))
    return BulkDeleteResponse(deleted_count=len(test_case_ids), deleted_ids=test_case_ids)


# =====================================================
# SAVE FROM ORCHESTRATOR
# =====================================================

@router.post("/save-from-orchestrator", response_model=SaveToRepositoryResponse)
async def save_from_orchestrator(
    save_data: SaveToRepositoryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save generated test cases from Orchestrator to the repository.
    Creates project and/or suite if specified by name.
    """
    logger.info(
        "Saving from orchestrator",
        user_id=current_user.id,
        test_case_count=len(save_data.test_cases),
        source_session_id=save_data.source_session_id
    )

    # Determine or create project
    if save_data.project_id:
        project_result = await db.execute(select(Project).where(Project.id == save_data.project_id))
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    elif save_data.project_name:
        # Create new project
        project = Project(
            name=save_data.project_name,
            created_by_id=current_user.id
        )
        db.add(project)
        await db.flush()  # Get the ID
    else:
        raise HTTPException(
            status_code=400,
            detail="Either project_id or project_name must be provided"
        )

    # Determine or create suite
    if save_data.suite_id:
        suite_result = await db.execute(select(TestSuite).where(TestSuite.id == save_data.suite_id))
        suite = suite_result.scalar_one_or_none()
        if not suite:
            raise HTTPException(status_code=404, detail="Test suite not found")
        if suite.project_id != project.id:
            raise HTTPException(
                status_code=400,
                detail="Suite does not belong to the specified project"
            )
    elif save_data.suite_name:
        # Get next position
        position_result = await db.execute(
            select(func.count()).select_from(
                select(TestSuite).where(
                    TestSuite.project_id == project.id,
                    TestSuite.parent_id.is_(None)
                ).subquery()
            )
        )
        position = position_result.scalar() or 0

        suite = TestSuite(
            name=save_data.suite_name,
            project_id=project.id,
            position=position,
            created_by_id=current_user.id
        )
        db.add(suite)
        await db.flush()  # Get the ID
    else:
        raise HTTPException(
            status_code=400,
            detail="Either suite_id or suite_name must be provided"
        )

    # Create test cases
    created_ids = []
    for tc_data in save_data.test_cases:
        # Override suite_id with the determined suite
        tc_data.suite_id = suite.id

        # Get next position
        position_result = await db.execute(
            select(func.count()).select_from(
                select(RepositoryTestCase).where(RepositoryTestCase.suite_id == suite.id).subquery()
            )
        )
        position = position_result.scalar() or 0

        test_case = RepositoryTestCase(
            suite_id=suite.id,
            external_id=tc_data.external_id,
            title=tc_data.title,
            description=tc_data.description,
            tc_type=tc_data.tc_type,
            priority=tc_data.priority,
            automation_status=tc_data.automation_status,
            estimated_minutes=tc_data.estimated_minutes,
            preconditions=tc_data.preconditions,
            steps=[step.model_dump() for step in (tc_data.steps or [])],
            expected_result=tc_data.expected_result,
            tags=tc_data.tags,
            custom_fields=tc_data.custom_fields,
            position=position,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
            source_session_id=save_data.source_session_id
        )
        db.add(test_case)
        await db.flush()
        created_ids.append(test_case.id)

    await db.commit()

    logger.info(
        "Saved from orchestrator",
        user_id=current_user.id,
        project_id=project.id,
        suite_id=suite.id,
        created_count=len(created_ids)
    )

    return SaveToRepositoryResponse(
        project_id=project.id,
        suite_id=suite.id,
        created_count=len(created_ids),
        test_case_ids=created_ids
    )


# =====================================================
# IMPORT / EXPORT
# =====================================================

@router.post("/test-cases/import", response_model=ImportResponse)
async def import_test_cases(
    import_data: ImportTestCaseRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Import test cases from a list"""
    logger.info("Importing test cases", user_id=current_user.id, count=len(import_data.test_cases))

    # Verify suite exists
    suite_result = await db.execute(select(TestSuite).where(TestSuite.id == import_data.suite_id))
    suite = suite_result.scalar_one_or_none()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    imported_count = 0
    updated_count = 0
    errors = []

    for tc_data in import_data.test_cases:
        try:
            # Check for existing test case with same external_id
            if tc_data.external_id:
                existing_result = await db.execute(
                    select(RepositoryTestCase).where(
                        RepositoryTestCase.suite_id == import_data.suite_id,
                        RepositoryTestCase.external_id == tc_data.external_id
                    )
                )
                existing = existing_result.scalar_one_or_none()

                if existing:
                    if import_data.overwrite:
                        # Update existing
                        update_dict = tc_data.model_dump(exclude_unset=True, exclude={"suite_id"})
                        if "steps" in update_dict and update_dict["steps"]:
                            update_dict["steps"] = [s.model_dump() for s in tc_data.steps]

                        for field, value in update_dict.items():
                            setattr(existing, field, value)

                        existing.updated_by_id = current_user.id
                        existing.version += 1
                        updated_count += 1
                    else:
                        errors.append(f"Test case with external_id '{tc_data.external_id}' already exists")
                        continue
                else:
                    # Create new
                    position_result = await db.execute(
                        select(func.count()).select_from(
                            select(RepositoryTestCase).where(
                                RepositoryTestCase.suite_id == import_data.suite_id
                            ).subquery()
                        )
                    )
                    position = position_result.scalar() or 0

                    test_case = RepositoryTestCase(
                        suite_id=import_data.suite_id,
                        external_id=tc_data.external_id,
                        title=tc_data.title,
                        description=tc_data.description,
                        tc_type=tc_data.tc_type,
                        priority=tc_data.priority,
                        automation_status=tc_data.automation_status,
                        estimated_minutes=tc_data.estimated_minutes,
                        preconditions=tc_data.preconditions,
                        steps=[s.model_dump() for s in (tc_data.steps or [])],
                        expected_result=tc_data.expected_result,
                        tags=tc_data.tags,
                        custom_fields=tc_data.custom_fields,
                        position=position,
                        created_by_id=current_user.id,
                        updated_by_id=current_user.id
                    )
                    db.add(test_case)
                    imported_count += 1
            else:
                # No external_id, create new
                position_result = await db.execute(
                    select(func.count()).select_from(
                        select(RepositoryTestCase).where(
                            RepositoryTestCase.suite_id == import_data.suite_id
                        ).subquery()
                    )
                )
                position = position_result.scalar() or 0

                test_case = RepositoryTestCase(
                    suite_id=import_data.suite_id,
                    title=tc_data.title,
                    description=tc_data.description,
                    tc_type=tc_data.tc_type,
                    priority=tc_data.priority,
                    automation_status=tc_data.automation_status,
                    estimated_minutes=tc_data.estimated_minutes,
                    preconditions=tc_data.preconditions,
                    steps=[s.model_dump() for s in (tc_data.steps or [])],
                    expected_result=tc_data.expected_result,
                    tags=tc_data.tags,
                    custom_fields=tc_data.custom_fields,
                    position=position,
                    created_by_id=current_user.id,
                    updated_by_id=current_user.id
                )
                db.add(test_case)
                imported_count += 1

        except Exception as e:
            errors.append(f"Error importing '{tc_data.title}': {str(e)}")

    await db.commit()

    logger.info(
        "Import completed",
        user_id=current_user.id,
        imported_count=imported_count,
        updated_count=updated_count,
        failed_count=len(errors)
    )

    return ImportResponse(
        imported_count=imported_count,
        updated_count=updated_count,
        failed_count=len(errors),
        errors=errors
    )


@router.post("/test-cases/export")
async def export_test_cases(
    export_data: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export test cases as JSON or CSV"""
    # Build query
    query = select(RepositoryTestCase)

    if export_data.suite_id:
        query = query.where(RepositoryTestCase.suite_id == export_data.suite_id)
    elif export_data.project_id:
        query = query.where(
            RepositoryTestCase.suite_id.in_(
                select(TestSuite.id).where(TestSuite.project_id == export_data.project_id)
            )
        )

    result = await db.execute(query.order_by(RepositoryTestCase.position))
    test_cases = result.scalars().all()

    if export_data.format == "json":
        return {
            "test_cases": [RepositoryTestCaseResponse.model_validate(tc) for tc in test_cases],
            "total": len(test_cases),
            "format": "json"
        }
    else:  # CSV
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "ID", "External ID", "Title", "Type", "Priority", "Automation Status",
            "Preconditions", "Steps", "Expected Result", "Tags"
        ])

        # Rows
        for tc in test_cases:
            steps_str = "; ".join([
                f"{s.get('step', '')}. {s.get('action', '')} -> {s.get('expected', '')}"
                for s in (tc.steps or [])
            ])

            writer.writerow([
                tc.id,
                tc.external_id or "",
                tc.title,
                tc.tc_type.value,
                tc.priority.value,
                tc.automation_status.value,
                "; ".join(tc.preconditions or []),
                steps_str,
                tc.expected_result or "",
                ", ".join(tc.tags or [])
            ])

        return {
            "data": output.getvalue(),
            "filename": f"test_cases_export_{len(test_cases)}_cases.csv",
            "content_type": "text/csv",
            "total": len(test_cases)
        }


# =====================================================
# STATS
# =====================================================

@router.get("/stats")
async def get_repository_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get repository statistics for the current user
    """
    logger.info("Fetching repository stats", user_id=current_user.id)

    # Get user's projects
    projects_query = select(func.count(Project.id)).where(Project.created_by_id == current_user.id)
    projects_result = await db.execute(projects_query)
    total_projects = projects_result.scalar() or 0

    # Get user's suites
    suites_query = (
        select(func.count(TestSuite.id))
        .select_from(TestSuite)
        .join(Project, TestSuite.project_id == Project.id)
        .where(Project.created_by_id == current_user.id)
    )
    suites_result = await db.execute(suites_query)
    total_suites = suites_result.scalar() or 0

    # Get user's test cases
    test_cases_query = (
        select(func.count(RepositoryTestCase.id))
        .select_from(RepositoryTestCase)
        .join(TestSuite, RepositoryTestCase.suite_id == TestSuite.id)
        .join(Project, TestSuite.project_id == Project.id)
        .where(Project.created_by_id == current_user.id)
    )
    test_cases_result = await db.execute(test_cases_query)
    total_test_cases = test_cases_result.scalar() or 0

    # Get test cases saved this month
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    saved_month_query = (
        select(func.count(RepositoryTestCase.id))
        .select_from(RepositoryTestCase)
        .join(TestSuite, RepositoryTestCase.suite_id == TestSuite.id)
        .join(Project, TestSuite.project_id == Project.id)
        .where(
            Project.created_by_id == current_user.id,
            RepositoryTestCase.created_at >= month_start
        )
    )
    saved_month_result = await db.execute(saved_month_query)
    saved_this_month = saved_month_result.scalar() or 0

    return {
        "total_projects": total_projects,
        "total_suites": total_suites,
        "total_test_cases": total_test_cases,
        "saved_this_month": saved_this_month
    }


# =====================================================
# VERSION CONTROL
# =====================================================

@router.get("/test-cases/{test_case_id}/versions", response_model=TestCaseVersionListResponse)
async def get_test_case_versions(
    test_case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get version history for a test case"""
    # Verify test case exists
    tc_result = await db.execute(select(RepositoryTestCase).where(RepositoryTestCase.id == test_case_id))
    test_case = tc_result.scalar_one_or_none()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    # Get versions (excluding deleted ones), ordered by version descending (newest first)
    versions_result = await db.execute(
        select(TestCaseVersion)
        .where(TestCaseVersion.test_case_id == test_case_id, TestCaseVersion.is_deleted == False)
        .order_by(TestCaseVersion.version.desc())
    )
    versions = versions_result.scalars().all()

    return TestCaseVersionListResponse(
        versions=[TestCaseVersionResponse.model_validate(v) for v in versions],
        total=len(versions)
    )


@router.post("/test-cases/{test_case_id}/versions/{version_id}/restore", response_model=RepositoryTestCaseResponse)
async def restore_test_case_version(
    test_case_id: int,
    version_id: int,
    restore_data: RestoreVersionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Restore a test case to a previous version"""
    # Verify test case exists
    tc_result = await db.execute(select(RepositoryTestCase).where(RepositoryTestCase.id == test_case_id))
    test_case = tc_result.scalar_one_or_none()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    # Get the version to restore
    version_result = await db.execute(
        select(TestCaseVersion).where(
            TestCaseVersion.id == version_id,
            TestCaseVersion.test_case_id == test_case_id
        )
    )
    version = version_result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Create a new version entry with current state before restoring
    old_version = TestCaseVersion(
        test_case_id=test_case_id,
        version=test_case.version,
        title=test_case.title,
        description=test_case.description,
        tc_type=test_case.tc_type,
        priority=test_case.priority,
        automation_status=test_case.automation_status,
        estimated_minutes=test_case.estimated_minutes,
        preconditions=test_case.preconditions,
        steps=test_case.steps,
        expected_result=test_case.expected_result,
        tags=test_case.tags,
        custom_fields=test_case.custom_fields,
        change_summary="Before restore",
        changed_by_id=current_user.id,
    )
    db.add(old_version)

    # Restore the test case to the version state
    test_case.title = version.title
    test_case.description = version.description
    test_case.tc_type = version.tc_type
    test_case.priority = version.priority
    test_case.automation_status = version.automation_status
    test_case.estimated_minutes = version.estimated_minutes
    test_case.preconditions = version.preconditions
    test_case.steps = version.steps
    test_case.expected_result = version.expected_result
    test_case.tags = version.tags
    test_case.custom_fields = version.custom_fields
    test_case.version = test_case.version + 1
    test_case.updated_by_id = current_user.id

    await db.commit()
    await db.refresh(test_case)

    logger.info(
        "Restored test case version",
        user_id=current_user.id,
        test_case_id=test_case_id,
        restored_from_version=version.version,
        new_version=test_case.version
    )

    return RepositoryTestCaseResponse.model_validate(test_case)

