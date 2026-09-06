from typing import List, Dict, Any
import os
from pathlib import Path
from .base import DocumentSource, DocumentType, RawDocument, ParsedDocument, Requirement
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PDFDocumentAdapter(DocumentSource):
    """
    Adapter for PDF and Word documents

    Handles: .pdf, .docx files
    Uses: PyPDF for PDF, python-docx for Word documents
    """

    @property
    def source_type(self) -> DocumentType:
        return DocumentType.PDF

    async def fetch(self, source_id: str, **kwargs) -> RawDocument:
        """
        Fetch PDF/Word document from file path

        Args:
            source_id: File path
            **kwargs: Additional metadata

        Returns:
            RawDocument with file bytes
        """
        file_path = Path(source_id)

        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {source_id}")

        # Determine file type
        extension = file_path.suffix.lower()
        if extension == ".pdf":
            doc_type = DocumentType.PDF
        elif extension in [".docx", ".doc"]:
            doc_type = DocumentType.WORD
        else:
            raise ValueError(f"Unsupported file type: {extension}")

        # Read file content
        with open(file_path, "rb") as f:
            content = f.read()

        logger.info(
            f"Fetched document: {file_path.name}",
            filename=file_path.name,
            size_bytes=len(content),
            doc_type=doc_type.value
        )

        return RawDocument(
            source_type=doc_type,
            content=content,
            filename=file_path.name,
            metadata={
                "file_size": len(content),
                "extension": extension,
                **kwargs
            }
        )

    async def parse(self, raw_doc: RawDocument) -> ParsedDocument:
        """
        Parse PDF or Word document into structured format

        Extracts:
        - Title (from filename or first heading)
        - Sections (headings + content)
        - Full text

        Args:
            raw_doc: Raw document with file bytes

        Returns:
            ParsedDocument with structured content
        """
        if raw_doc.source_type == DocumentType.PDF:
            return await self._parse_pdf(raw_doc)
        elif raw_doc.source_type == DocumentType.WORD:
            return await self._parse_docx(raw_doc)
        else:
            raise ValueError(f"Unsupported document type: {raw_doc.source_type}")

    async def _parse_pdf(self, raw_doc: RawDocument) -> ParsedDocument:
        """Parse PDF document"""
        from pypdf import PdfReader
        import io

        pdf_file = io.BytesIO(raw_doc.content)
        reader = PdfReader(pdf_file)

        # Extract text from all pages
        full_text = ""
        sections = []

        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            full_text += page_text + "\n\n"

            # Basic section detection (looking for headers)
            # This is simplified - could be enhanced with better header detection
            sections.append({
                "heading": f"Page {page_num}",
                "content": page_text
            })

        # Try to extract title from first page
        first_page_lines = sections[0]["content"].split("\n") if sections else []
        title = first_page_lines[0].strip() if first_page_lines else raw_doc.filename

        logger.info(
            f"Parsed PDF: {raw_doc.filename}",
            pages=len(reader.pages),
            sections=len(sections),
            text_length=len(full_text)
        )

        return ParsedDocument(
            source_type=DocumentType.PDF,
            title=title,
            sections=sections,
            full_text=full_text,
            metadata={
                "pages": len(reader.pages),
                "filename": raw_doc.filename,
                **raw_doc.metadata
            }
        )

    async def _parse_docx(self, raw_doc: RawDocument) -> ParsedDocument:
        """Parse Word document"""
        from docx import Document
        import io

        docx_file = io.BytesIO(raw_doc.content)
        doc = Document(docx_file)

        # Extract text and detect sections
        full_text = ""
        sections = []
        current_section = {"heading": "Introduction", "content": ""}

        for para in doc.paragraphs:
            text = para.text.strip()

            if not text:
                continue

            # Detect headings (simplified - checks for bold, large font)
            is_heading = False
            if para.style.name.startswith("Heading"):
                is_heading = True
            elif para.runs and para.runs[0].bold and len(text) < 100:
                is_heading = True

            if is_heading:
                # Save previous section
                if current_section["content"]:
                    sections.append(current_section)

                # Start new section
                current_section = {
                    "heading": text,
                    "content": ""
                }
            else:
                current_section["content"] += text + "\n"

            full_text += text + "\n"

        # Add last section
        if current_section["content"]:
            sections.append(current_section)

        # Extract title from document properties or first heading
        title = doc.core_properties.title or sections[0]["heading"] if sections else raw_doc.filename

        logger.info(
            f"Parsed Word document: {raw_doc.filename}",
            paragraphs=len(doc.paragraphs),
            sections=len(sections),
            text_length=len(full_text)
        )

        return ParsedDocument(
            source_type=DocumentType.WORD,
            title=title,
            sections=sections,
            full_text=full_text,
            metadata={
                "paragraphs": len(doc.paragraphs),
                "filename": raw_doc.filename,
                **raw_doc.metadata
            }
        )

    async def extract_requirements(self, parsed_doc: ParsedDocument) -> List[Requirement]:
        """
        Extract requirements using LLM

        Analyzes document sections and uses LLM to identify:
        - Features and requirements
        - Acceptance criteria
        - User stories
        - Constraints

        Args:
            parsed_doc: Parsed document

        Returns:
            List of extracted requirements
        """
        from app.pipeline.llm.llm_router import get_llm_client
        from app.core.config import settings

        llm_client = get_llm_client(settings.DEFAULT_LLM_MODEL)

        # Build prompt for requirement extraction
        prompt = f"""
You are a QA analyst extracting requirements from a product document.

Document Title: {parsed_doc.title}

Document Content:
{parsed_doc.full_text[:5000]}  # Limit to avoid token overflow

Your task:
1. Identify all features, requirements, and user stories
2. Extract acceptance criteria for each
3. Categorize by priority (high/medium/low) if mentioned
4. Add relevant tags

Output format (JSON array):
[
  {{
    "title": "Feature name",
    "description": "Detailed description",
    "section": "Section where found",
    "acceptance_criteria": ["criterion 1", "criterion 2"],
    "priority": "high/medium/low",
    "tags": ["tag1", "tag2"]
  }}
]

ONLY JSON OUTPUT, NO EXPLANATIONS.
"""

        try:
            response = await llm_client.generate(prompt)

            # Parse JSON response
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                requirements_data = json.loads(json_match.group())

                requirements = [
                    Requirement(
                        title=req.get("title", "Untitled"),
                        description=req.get("description", ""),
                        section=req.get("section"),
                        acceptance_criteria=req.get("acceptance_criteria", []),
                        priority=req.get("priority"),
                        tags=req.get("tags", []),
                        metadata={"source": parsed_doc.title}
                    )
                    for req in requirements_data
                ]

                logger.info(
                    f"Extracted requirements from {parsed_doc.title}",
                    count=len(requirements)
                )

                return requirements

            else:
                logger.warning("Failed to extract JSON from LLM response")
                return []

        except Exception as e:
            logger.error(f"Error extracting requirements: {e}", exc_info=True)
            return []


# Register adapter with global processor
from .base import document_processor
pdf_adapter = PDFDocumentAdapter()
document_processor.register_adapter(pdf_adapter)


class WordDocumentAdapter(PDFDocumentAdapter):
    """Route .docx through the PDF adapter — it already parses Word files
    (python-docx branch in parse())."""

    @property
    def source_type(self) -> DocumentType:
        return DocumentType.WORD
