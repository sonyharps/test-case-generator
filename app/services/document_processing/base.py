from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types"""
    PDF = "pdf"
    WORD = "docx"
    MARKDOWN = "md"
    TEXT = "txt"
    FIGMA = "figma"
    JIRA = "jira"
    LINEAR = "linear"
    CONFLUENCE = "confluence"


class ProcessingStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RawDocument:
    """Raw document data before processing"""
    source_type: DocumentType
    content: Any  # File bytes, API response, URL, etc.
    filename: Optional[str] = None
    source_url: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ParsedDocument:
    """Parsed and structured document"""
    source_type: DocumentType
    title: str
    sections: List[Dict[str, str]]  # [{"heading": "...", "content": "..."}]
    full_text: str
    metadata: Dict[str, Any]
    extracted_at: datetime = None

    def __post_init__(self):
        if self.extracted_at is None:
            self.extracted_at = datetime.utcnow()


@dataclass
class Requirement:
    """Extracted requirement/feature"""
    title: str
    description: str
    section: Optional[str] = None
    acceptance_criteria: List[str] = None
    priority: Optional[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DocumentChunk:
    """Text chunk for vector storage"""
    text: str
    metadata: Dict[str, Any]
    chunk_index: int
    embedding: Optional[List[float]] = None


class DocumentSource(ABC):
    """
    Abstract base class for all document sources

    All document adapters (PDF, Figma, JIRA, etc.) must implement this interface
    This ensures consistent processing pipeline regardless of source
    """

    @property
    @abstractmethod
    def source_type(self) -> DocumentType:
        """Return the document type this adapter handles"""
        pass

    @abstractmethod
    async def fetch(self, source_id: str, **kwargs) -> RawDocument:
        """
        Fetch document from source

        Args:
            source_id: File path, URL, or identifier
            **kwargs: Source-specific parameters

        Returns:
            RawDocument with raw content
        """
        pass

    @abstractmethod
    async def parse(self, raw_doc: RawDocument) -> ParsedDocument:
        """
        Parse raw document into structured format

        Args:
            raw_doc: Raw document from fetch()

        Returns:
            ParsedDocument with sections and full text
        """
        pass

    @abstractmethod
    async def extract_requirements(self, parsed_doc: ParsedDocument) -> List[Requirement]:
        """
        Extract requirements/features from parsed document

        Uses LLM to identify and structure requirements

        Args:
            parsed_doc: Parsed document from parse()

        Returns:
            List of extracted requirements
        """
        pass

    async def chunk_document(
        self,
        parsed_doc: ParsedDocument,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[DocumentChunk]:
        """
        Split document into chunks for vector storage

        Default implementation using recursive text splitting
        Can be overridden for source-specific chunking

        Args:
            parsed_doc: Parsed document
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks

        Returns:
            List of document chunks
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
        )

        chunks = splitter.split_text(parsed_doc.full_text)

        return [
            DocumentChunk(
                text=chunk,
                metadata={
                    "source_type": self.source_type.value,
                    "title": parsed_doc.title,
                    "chunk_index": idx,
                    **parsed_doc.metadata
                },
                chunk_index=idx
            )
            for idx, chunk in enumerate(chunks)
        ]


class DocumentProcessor:
    """
    Main document processing orchestrator

    Routes documents to appropriate source adapter
    Coordinates the full processing pipeline
    """

    def __init__(self):
        self.adapters: Dict[DocumentType, DocumentSource] = {}

    def register_adapter(self, adapter: DocumentSource):
        """Register a document source adapter"""
        self.adapters[adapter.source_type] = adapter

    def get_adapter(self, doc_type: DocumentType) -> DocumentSource:
        """Get adapter for document type"""
        adapter = self.adapters.get(doc_type)
        if not adapter:
            raise ValueError(f"No adapter registered for document type: {doc_type}")
        return adapter

    async def process_document(
        self,
        doc_type: DocumentType,
        source_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Full document processing pipeline

        1. Fetch raw document
        2. Parse into structured format
        3. Extract requirements (optional)
        4. Chunk for vector storage
        5. Generate embeddings

        Returns processing result with all artifacts
        """
        adapter = self.get_adapter(doc_type)

        # Step 1: Fetch
        raw_doc = await adapter.fetch(source_id, **kwargs)

        # Step 2: Parse
        parsed_doc = await adapter.parse(raw_doc)

        # Step 3: Extract requirements (optional, can be done later)
        requirements = []
        if kwargs.get("extract_requirements", False):
            requirements = await adapter.extract_requirements(parsed_doc)

        # Step 4: Chunk
        chunks = await adapter.chunk_document(
            parsed_doc,
            chunk_size=kwargs.get("chunk_size", 1000),
            chunk_overlap=kwargs.get("chunk_overlap", 200)
        )

        return {
            "parsed_doc": parsed_doc,
            "requirements": requirements,
            "chunks": chunks,
            "status": ProcessingStatus.COMPLETED
        }


# Global processor instance
document_processor = DocumentProcessor()
