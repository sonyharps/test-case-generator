from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    QAOrchestratorException,
    AuthenticationError,
    ValidationError,
    LLMProviderError,
    ParsingError,
    DatabaseError,
    PDFExportError
)
from app.core.logging_config import get_logger
import traceback

logger = get_logger(__name__)

async def qa_exception_handler(request: Request, exc: QAOrchestratorException):
    """Handle custom QA Orchestrator exceptions"""

    # Map exception types to status codes
    status_map = {
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        LLMProviderError: status.HTTP_503_SERVICE_UNAVAILABLE,
        ParsingError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        PDFExportError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    status_code = status_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Log error
    logger.error(
        "application_error",
        exception_type=type(exc).__name__,
        message=exc.message,
        details=exc.details,
        status_code=status_code
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "details": exc.details,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""

    logger.error(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        message=str(exc),
        traceback=traceback.format_exc()
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )
