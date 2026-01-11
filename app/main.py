from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.logging_config import setup_logging, get_logger
from app.api.v1.orchestrator.router import router as orch_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.history.router import router as history_router
from app.api.v1.requirements.router import router as requirements_router
from app.api.v1.analytics.router import router as analytics_router
from app.api.v1.documents.router import router as documents_router
from app.api.v1.rag.router import router as rag_router
from app.api.v1.test_cases.router import router as test_cases_router
from app.api.v1.dashboard.router import router as dashboard_router
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.exception_handler import qa_exception_handler, generic_exception_handler
from app.core.exceptions import QAOrchestratorException
from app.core.config import settings

# Setup logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="QA Orchestrator API",
    description="""
    AI-powered test case generation platform with enterprise features.

    ## Features
    - Username/Password authentication with JWT
    - AI-powered test case generation (Functional, Negative, Boundary)
    - PDF export with professional templates
    - Session history and analytics
    - Requirements library

    ## Authentication
    All endpoints (except auth) require Bearer token authentication.

    Use `/v1/auth/register` to create an account and `/v1/auth/login` to authenticate.
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User registration and login endpoints"
        },
        {
            "name": "orchestrator",
            "description": "AI test case generation and PDF export"
        },
        {
            "name": "history",
            "description": "Session history and retrieval"
        },
        {
            "name": "requirements",
            "description": "Requirements library management"
        },
        {
            "name": "analytics",
            "description": "Usage analytics and statistics"
        },
        {
            "name": "documents",
            "description": "Document upload and RAG processing (PRD, User Stories, etc.)"
        },
        {
            "name": "advanced-rag",
            "description": "Advanced RAG features: query expansion, semantic re-ranking, hybrid search, citations"
        },
        {
            "name": "test-cases",
            "description": "Test case management: inline editing, approval workflow, commenting"
        },
        {
            "name": "dashboard",
            "description": "User dashboard with statistics, recent activity, and analytics"
        }
    ]
)

# Middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL] if settings.FRONTEND_URL else ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(QAOrchestratorException, qa_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Routers
app.include_router(auth_router, prefix="/v1/auth", tags=["authentication"])
app.include_router(orch_router, prefix="/v1/orchestrator", tags=["orchestrator"])
app.include_router(history_router, prefix="/v1/history", tags=["history"])
app.include_router(requirements_router, prefix="/v1/requirements", tags=["requirements"])
app.include_router(analytics_router, prefix="/v1/analytics", tags=["analytics"])
app.include_router(documents_router, prefix="/v1/documents", tags=["documents"])
app.include_router(rag_router, prefix="/v1/rag", tags=["advanced-rag"])
app.include_router(test_cases_router, prefix="/v1", tags=["test-cases"])
app.include_router(dashboard_router, prefix="/v1/dashboard", tags=["dashboard"])
app.include_router(api_router)

@app.on_event("startup")
async def startup():
    logger.info("application_startup", version="2.0.0")

@app.on_event("shutdown")
async def shutdown():
    logger.info("application_shutdown")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}
