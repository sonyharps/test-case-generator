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

# Import adapters to trigger registration.
# pdf_adapter covers PDF (registered by source_type) and registers a WORD
# subclass below; docx parsing itself lives in PDFDocumentAdapter.
from . import pdf_adapter  # noqa: F401
from . import text_adapter  # noqa: F401   # .txt / .md
from . import image_adapter  # noqa: F401  # .png / .jpg / .jpeg (Figma export, mockup)

from .base import document_processor, DocumentType  # noqa: E402

# .docx has its parser inside PDFDocumentAdapter (python-docx branch) — expose
# it under the WORD type so the registry can route it.
_word_adapter = pdf_adapter.WordDocumentAdapter()
document_processor.register_adapter(_word_adapter)

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
