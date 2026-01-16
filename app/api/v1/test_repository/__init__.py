from .router import router
from .test_runs_router import router as test_runs_router
from .reports_router import router as reports_router

__all__ = ["router", "test_runs_router", "reports_router"]
