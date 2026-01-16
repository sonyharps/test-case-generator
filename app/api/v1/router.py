from fastapi import APIRouter
from app.api.v1.orchestrator.router import router as orchestrator_router
from app.api.v1.llm.router import router as llm_router
from app.api.v1.test_repository import router as test_repository_router, test_runs_router, reports_router
# Legacy API disabled
# from app.api.v1.legacy.router import router as legacy_router
from app.api.v1.orchestrator.router import router as orch_router


router = APIRouter()

router = APIRouter()
router.include_router(orchestrator_router)
router.include_router(llm_router, prefix="/llm", tags=["llm"])
router.include_router(test_repository_router, prefix="/test-repository", tags=["test-repository"])
router.include_router(test_runs_router, prefix="/test-repository", tags=["test-repository"])
router.include_router(reports_router, prefix="/test-repository", tags=["test-repository"])
# router.include_router(legacy_router)

# router.include_router(orchestrator_router, prefix="/v1")
# router.include_router(legacy_router, prefix="/v1/legacy")
# router.include_router(orch_router, prefix="/orchestrator", tags=["Orchestrator"])
