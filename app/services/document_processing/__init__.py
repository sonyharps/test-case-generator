# Document processing framework
from .base import (
    DocumentType,
    ProcessingStatus,
    RawDocument,
    ParsedDocument,
    Requirement,
    DocumentChunk,
    DocumentSource,
    DocumentProcessor,
    document_processor
)

# Import adapters to trigger registration
from . import pdf_adapter  # noqa: F401

__all__ = [
    "DocumentType",
    "ProcessingStatus",
    "RawDocument",
    "ParsedDocument",
    "Requirement",
    "DocumentChunk",
    "DocumentSource",
    "DocumentProcessor",
    "document_processor"
]
