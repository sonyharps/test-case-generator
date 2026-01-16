"""Test Reports API Router

Endpoints for test execution reports and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, literal_column, cast, Numeric
from typing import Optional, List
from datetime import datetime, timedelta

from app.db.session import get_db
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from app.models.test_repository import (
    Project,
    TestRun,
    TestResult,
    RepositoryTestCase,
    TestSuite,
    TestRunStatus,
    TestResultStatus,
)
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/reports/overview")
async def get_project_overview(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overview statistics for a project
    - Total test cases
    - Total test runs
    - Overall pass rate
    - Recent activity
    """
    # Verify project exists
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get total test cases count
    tc_query = select(func.count()).select_from(
        select(RepositoryTestCase).where(
            RepositoryTestCase.suite_id.in_(
                select(TestSuite.id).where(TestSuite.project_id == project_id)
            )
        ).subquery()
    )
    tc_result = await db.execute(tc_query)
    total_test_cases = tc_result.scalar() or 0

    # Get total test runs count
    runs_query = select(func.count()).select_from(
        select(TestRun).where(TestRun.project_id == project_id).subquery()
    )
    runs_result = await db.execute(runs_query)
    total_test_runs = runs_result.scalar() or 0

    # Get overall pass rate (from all completed runs)
    pass_rate_query = select(
        func.round(
            cast(
                func.sum(
                    case(
                        (TestResult.status == TestResultStatus.PASSED, 1),
                        else_=0
                    )
                ) * 100.0 / func.count(),
                Numeric
            ),
            1
        )
    ).select_from(
        select(TestResult).where(
            TestResult.test_run_id.in_(
                select(TestRun.id).where(
                    and_(
                        TestRun.project_id == project_id,
                        TestRun.status == TestRunStatus.COMPLETED
                    )
                )
            )
        ).subquery()
    )
    pass_rate_result = await db.execute(pass_rate_query)
    overall_pass_rate = pass_rate_result.scalar() or 0

    # Get recent test runs (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_query = select(TestRun).where(
        and_(
            TestRun.project_id == project_id,
            TestRun.created_at >= seven_days_ago
        )
    ).order_by(TestRun.created_at.desc()).limit(5)
    recent_result = await db.execute(recent_query)
    recent_runs = recent_result.scalars().all()

    # Get test case breakdown by type
    type_query = select(
        RepositoryTestCase.tc_type,
        func.count().label('count')
    ).where(
        RepositoryTestCase.suite_id.in_(
            select(TestSuite.id).where(TestSuite.project_id == project_id)
        )
    ).group_by(RepositoryTestCase.tc_type)
    type_result = await db.execute(type_query)
    by_type = {row.tc_type: row.count for row in type_result}

    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_test_cases": total_test_cases,
        "total_test_runs": total_test_runs,
        "overall_pass_rate": float(overall_pass_rate),
        "test_cases_by_type": by_type,
        "recent_runs_count": len(recent_runs)
    }


@router.get("/reports/pass-rate-trend")
async def get_pass_rate_trend(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
):
    """
    Get pass rate trend over time
    Returns daily aggregated results for the specified period
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get completed test runs in the period
    runs_query = select(TestRun).where(
        and_(
            TestRun.project_id == project_id,
            TestRun.status == TestRunStatus.COMPLETED,
            TestRun.completed_at >= start_date
        )
    ).order_by(TestRun.completed_at)
    runs_result = await db.execute(runs_query)
    runs = runs_result.scalars().all()

    # Group by date
    trend_by_date = {}
    for run in runs:
        if run.completed_at:
            date_key = run.completed_at.date().isoformat()

            # Get results for this run
            results_query = select(TestResult).where(TestResult.test_run_id == run.id)
            results_result = await db.execute(results_query)
            results = results_result.scalars().all()

            passed = sum(1 for r in results if r.status == TestResultStatus.PASSED)
            total = len(results)
            pass_rate = (passed / total * 100) if total > 0 else 0

            if date_key not in trend_by_date:
                trend_by_date[date_key] = {
                    "date": date_key,
                    "runs": 0,
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0,
                    "pass_rate": 0
                }

            trend_by_date[date_key]["runs"] += 1
            trend_by_date[date_key]["total_tests"] += total
            trend_by_date[date_key]["passed"] += passed
            trend_by_date[date_key]["failed"] += total - passed

    # Calculate aggregated pass rate per date
    trend_data = []
    for date_data in sorted(trend_by_date.values(), key=lambda x: x["date"]):
        total = date_data["total_tests"]
        date_data["pass_rate"] = round((date_data["passed"] / total * 100), 1) if total > 0 else 0
        trend_data.append(date_data)

    return {
        "project_id": project_id,
        "period_days": days,
        "data": trend_data
    }


@router.get("/reports/execution-summary")
async def get_execution_summary(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[TestRunStatus] = Query(None, description="Filter by run status"),
):
    """
    Get execution summary with aggregated stats
    """
    query = select(TestRun).where(TestRun.project_id == project_id)

    if status:
        query = query.where(TestRun.status == status)

    query = query.order_by(TestRun.created_at.desc())
    result = await db.execute(query)
    runs = result.scalars().all()

    summaries = []
    for run in runs:
        # Get results
        results_query = select(TestResult).where(TestResult.test_run_id == run.id)
        results_result = await db.execute(results_query)
        results = results_result.scalars().all()

        total = len(results)
        passed = sum(1 for r in results if r.status == TestResultStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestResultStatus.FAILED)
        blocked = sum(1 for r in results if r.status == TestResultStatus.BLOCKED)
        skipped = sum(1 for r in results if r.status == TestResultStatus.SKIPPED)
        pending = sum(1 for r in results if r.status == TestResultStatus.PENDING)
        retest = sum(1 for r in results if r.status == TestResultStatus.RETEST)

        summaries.append({
            "run_id": run.id,
            "run_name": run.name,
            "status": run.status,
            "created_at": run.created_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "total": total,
            "passed": passed,
            "failed": failed,
            "blocked": blocked,
            "skipped": skipped,
            "pending": pending + retest,
            "pass_rate": round((passed / total * 100), 1) if total > 0 else 0
        })

    return {
        "project_id": project_id,
        "summaries": summaries,
        "total": len(summaries)
    }


@router.get("/reports/test-case-coverage")
async def get_test_case_coverage(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get test case coverage breakdown
    - Coverage by suite
    - Coverage by type
    - Most frequently used test cases
    """
    # Get all suites in project
    suites_query = select(TestSuite).where(TestSuite.project_id == project_id)
    suites_result = await db.execute(suites_query)
    suites = suites_result.scalars().all()

    suite_coverage = []
    for suite in suites:
        # Get test case count
        tc_query = select(func.count()).select_from(
            select(RepositoryTestCase).where(RepositoryTestCase.suite_id == suite.id).subquery()
        )
        tc_result = await db.execute(tc_query)
        case_count = tc_result.scalar() or 0

        # Get execution count (how many times cases from this suite were run)
        exec_query = select(func.count()).select_from(
            select(TestResult).where(
                TestResult.test_case_id.in_(
                    select(RepositoryTestCase.id).where(RepositoryTestCase.suite_id == suite.id)
                )
            ).subquery()
        )
        exec_result = await db.execute(exec_query)
        execution_count = exec_result.scalar() or 0

        suite_coverage.append({
            "suite_id": suite.id,
            "suite_name": suite.name,
            "test_case_count": case_count,
            "execution_count": execution_count
        })

    # Coverage by type
    type_query = select(
        RepositoryTestCase.tc_type,
        func.count().label('count')
    ).where(
        RepositoryTestCase.suite_id.in_(
            select(TestSuite.id).where(TestSuite.project_id == project_id)
        )
    ).group_by(RepositoryTestCase.tc_type)
    type_result = await db.execute(type_query)
    by_type = [{ "type": row.tc_type, "count": row.count } for row in type_result]

    return {
        "project_id": project_id,
        "suite_coverage": suite_coverage,
        "coverage_by_type": by_type
    }


@router.get("/reports/failing-tests")
async def get_failing_tests(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, description="Max number of results", ge=1, le=100),
):
    """
    Get most frequently failing test cases
    """
    # Get failed results from the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    failing_query = select(
        RepositoryTestCase.id,
        RepositoryTestCase.title,
        RepositoryTestCase.suite_id,
        func.count().label('fail_count')
    ).join(
        TestResult, TestResult.test_case_id == RepositoryTestCase.id
    ).join(
        TestRun, TestRun.id == TestResult.test_run_id
    ).where(
        and_(
            TestRun.project_id == project_id,
            TestResult.status == TestResultStatus.FAILED,
            TestResult.created_at >= thirty_days_ago
        )
    ).group_by(
        RepositoryTestCase.id,
        RepositoryTestCase.title,
        RepositoryTestCase.suite_id
    ).order_by(
        func.count().desc()
    ).limit(limit)

    failing_result = await db.execute(failing_query)
    failing_tests = [
        {
            "test_case_id": row.id,
            "title": row.title,
            "suite_id": row.suite_id,
            "fail_count": row.fail_count
        }
        for row in failing_result
    ]

    return {
        "project_id": project_id,
        "period_days": 30,
        "failing_tests": failing_tests
    }


@router.get("/reports/run/{test_run_id}/export")
async def export_test_run_report(
    test_run_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export test run report with full details
    Can be used to generate PDF or other formats
    """
    # Get test run with results
    run_result = await db.execute(
        select(TestRun).where(TestRun.id == test_run_id)
    )
    run = run_result.scalar_one_or_none()

    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    # Get results with test cases
    results_query = select(TestResult).where(TestResult.test_run_id == test_run_id)
    results_result = await db.execute(results_query)
    results = results_result.scalars().all()

    # Build export data
    export_data = {
        "run": {
            "id": run.id,
            "name": run.name,
            "description": run.description,
            "status": run.status,
            "created_at": run.created_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        },
        "summary": run.progress,
        "results": []
    }

    for result in results:
        # Get test case details
        tc_query = select(RepositoryTestCase).where(RepositoryTestCase.id == result.test_case_id)
        tc_result = await db.execute(tc_query)
        tc = tc_result.scalar_one_or_none()

        export_data["results"].append({
            "test_case": {
                "id": tc.id if tc else None,
                "title": tc.title if tc else "Unknown",
                "external_id": tc.external_id if tc else None,
                "priority": tc.priority.value if tc else None,
                "type": tc.tc_type.value if tc else None,
            } if tc else None,
            "result": {
                "status": result.status,
                "executed_at": result.executed_at.isoformat() if result.executed_at else None,
                "comments": result.comments,
                "actual_result": result.actual_result,
                "defects": result.defects,
                "execution_seconds": result.execution_seconds,
            }
        })

    return export_data
