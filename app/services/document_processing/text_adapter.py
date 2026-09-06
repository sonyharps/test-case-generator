"""Plain-text & Markdown document adapter (.txt, .md).

Handles documents whose content is already text — user stories, requirement
notes, exported backlog items. Sections are split on markdown-style headings
(``#``-``######``) when present; otherwise the whole text is one section.
"""
import re
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

_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)")


class TextDocumentAdapter(DocumentSource):
    def __init__(self, doc_type: DocumentType):
        self._doc_type = doc_type

    @property
    def source_type(self) -> DocumentType:
        return self._doc_type

    async def fetch(self, source_id: str, **kwargs) -> RawDocument:
        file_path = Path(source_id)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {source_id}")
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return RawDocument(
            source_type=self._doc_type,
            content=content,
            filename=file_path.name,
        )

    async def parse(self, raw_doc: RawDocument) -> ParsedDocument:
        text = raw_doc.content
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="replace")
        text = text.strip()

        first_line = text.splitlines()[0].strip() if text else ""
        title = _HEADING_RE.match(first_line).group(1).strip() if _HEADING_RE.match(first_line) else first_line
        title = (title or raw_doc.filename or "Dokumen teks")[:120]

        sections: List[dict] = []
        current_heading = title
        current_lines: List[str] = []

        for line in text.splitlines():
            m = _HEADING_RE.match(line.strip())
            if m:
                if current_lines:
                    sections.append({
                        "heading": current_heading,
                        "content": "\n".join(current_lines).strip(),
                    })
                current_heading = m.group(1).strip()
                current_lines = []
            else:
                current_lines.append(line)
        if current_lines:
            sections.append({
                "heading": current_heading,
                "content": "\n".join(current_lines).strip(),
            })

        if not sections:
            sections = [{"heading": title, "content": text}]

        logger.info(
            "Parsed text document",
            filename=raw_doc.filename,
            sections=len(sections),
            chars=len(text),
        )
        return ParsedDocument(
            source_type=self._doc_type,
            title=title,
            sections=sections,
            full_text=text,
            metadata={"filename": raw_doc.filename, "encoding": "utf-8"},
        )

    async def extract_requirements(self, parsed_doc: ParsedDocument) -> List[Requirement]:
        # Text documents flow into generation via their full text chunks;
        # structured requirement extraction is reserved for PDF/Word PRDs.
        return []

    async def chunk_document(
        self, parsed_doc: ParsedDocument, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        buffer = ""

        def flush():
            nonlocal buffer
            if buffer.strip():
                chunks.append(DocumentChunk(
                    text=buffer.strip(),
                    metadata={"source": parsed_doc.title},
                    chunk_index=len(chunks),
                ))
            buffer = ""

        # Chunk per-section first (keeps user stories / headings together),
        # splitting oversized sections on word boundaries.
        for section in parsed_doc.sections:
            piece = f"{section['heading']}\n{section.get('content', '')}".strip()
            if len(piece) <= chunk_size:
                if len(buffer) + len(piece) + 2 > chunk_size:
                    flush()
                buffer = f"{buffer}\n\n{piece}" if buffer else piece
            else:
                flush()
                words = piece.split()
                line = ""
                for w in words:
                    if len(line) + len(w) + 1 > chunk_size:
                        chunks.append(DocumentChunk(
                            text=line,
                            metadata={"source": parsed_doc.title},
                            chunk_index=len(chunks),
                        ))
                        line = w
                    else:
                        line = f"{line} {w}".strip()
                if line:
                    chunks.append(DocumentChunk(
                        text=line,
                        metadata={"source": parsed_doc.title},
                        chunk_index=len(chunks),
                    ))
        flush()
        return chunks


# Register adapters for the text-based types
from .base import document_processor  # noqa: E402

document_processor.register_adapter(TextDocumentAdapter(DocumentType.TEXT))
document_processor.register_adapter(TextDocumentAdapter(DocumentType.MARKDOWN))
