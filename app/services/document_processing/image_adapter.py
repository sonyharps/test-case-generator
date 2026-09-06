"""Image document adapter (.png, .jpg, .jpeg) — Figma exports & UI mockups.

Images carry no extractable text, so the parsed document is a short,
explicit placeholder that tells the generation pipeline a *visual* artifact
accompanies the requirement docs (PRD / user story). The filename becomes
the title and is kept in the context so the LLM can reference the mockup.
"""
from pathlib import Path
from typing import List

from .base import (
    DocumentChunk,
    DocumentSource,
    DocumentType,
    ParsedDocument,
    RawDocument,
    Requirement,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_PLACEHOLDER = (
    "[Dokumen visual — mockup/gambar: {filename}]\n"
    "Dokumen ini adalah mockup visual (export Figma/screenshot UI). Tidak ada teks "
    "yang bisa diekstrak dari file gambar — gunakan sebagai referensi tampilan dan "
    "alur UI, dipakai bersama dokumen PRD/user story yang menyertainya."
)


class ImageDocumentAdapter(DocumentSource):
    def __init__(self, doc_type: DocumentType):
        self._doc_type = doc_type

    @property
    def source_type(self) -> DocumentType:
        return self._doc_type

    async def fetch(self, source_id: str, **kwargs) -> RawDocument:
        file_path = Path(source_id)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {source_id}")
        content = file_path.read_bytes()
        return RawDocument(
            source_type=self._doc_type,
            content=content,
            filename=file_path.name,
        )

    async def parse(self, raw_doc: RawDocument) -> ParsedDocument:
        name = raw_doc.filename or "mockup"
        title = Path(name).stem.replace("-", " ").replace("_", " ").title()
        text = _PLACEHOLDER.format(filename=name)

        logger.info("Parsed image document", filename=name)
        return ParsedDocument(
            source_type=self._doc_type,
            title=title,
            sections=[{"heading": title, "content": text}],
            full_text=text,
            metadata={"filename": name, "visual": True},
        )

    async def extract_requirements(self, parsed_doc: ParsedDocument) -> List[Requirement]:
        return []

    async def chunk_document(
        self, parsed_doc: ParsedDocument, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[DocumentChunk]:
        return [
            DocumentChunk(
                text=parsed_doc.full_text,
                metadata={"source": parsed_doc.title, "visual": True},
                chunk_index=0,
            )
        ]


# Register adapters for the image types
from .base import document_processor  # noqa: E402

document_processor.register_adapter(ImageDocumentAdapter(DocumentType.PNG))
document_processor.register_adapter(ImageDocumentAdapter(DocumentType.JPG))
document_processor.register_adapter(ImageDocumentAdapter(DocumentType.JPEG))
