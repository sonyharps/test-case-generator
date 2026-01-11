from typing import Any, Optional

class QAOrchestratorException(Exception):
    """Base exception for QA Orchestrator"""
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(QAOrchestratorException):
    """Authentication/authorization errors"""
    pass

class ValidationError(QAOrchestratorException):
    """Input validation errors"""
    pass

class LLMProviderError(QAOrchestratorException):
    """LLM provider communication errors"""
    pass

class ParsingError(QAOrchestratorException):
    """JSON/output parsing errors"""
    pass

class DatabaseError(QAOrchestratorException):
    """Database operation errors"""
    pass

class PDFExportError(QAOrchestratorException):
    """PDF generation errors"""
    pass
