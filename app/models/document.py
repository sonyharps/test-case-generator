from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import enum


class DocumentType(str, enum.Enum):
    """Document source types"""
    PDF = "pdf"
    WORD = "docx"
    MARKDOWN = "md"
    TEXT = "txt"
    FIGMA = "figma"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    JIRA = "jira"
    LINEAR = "linear"


class ProcessingStatus(str, enum.Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadedDocument(Base, TimestampMixin):
    """
    Uploaded documents (PRD, user stories, design specs)

    Stores metadata about uploaded documents and links to:
    - Vector embeddings in Qdrant
    - Extracted requirements
    - Generated test cases
    """
    __tablename__ = "uploaded_documents"

    id = Column(Integer, primary_key=True, index=True)

    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="documents")

    # Document metadata
    filename = Column(String(500), nullable=False)
    file_type = Column(SQLEnum(DocumentType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    file_size = Column(Integer)  # bytes
    file_path = Column(String(1000))  # Local storage path
    source_url = Column(String(1000))  # For external sources (Figma, JIRA, etc.)

    # Processing
    processing_status = Column(SQLEnum(ProcessingStatus, values_callable=lambda x: [e.value for e in x]), default=ProcessingStatus.PENDING)
    error_message = Column(Text)

    # Content
    title = Column(String(500))
    content_preview = Column(Text)  # First 500 chars for display
    full_text = Column(Text)  # Full extracted text

    # Structured data
    sections = Column(JSON)  # [{"heading": "...", "content": "..."}]
    extracted_requirements = Column(JSON)  # List of requirement dicts

    # Vector storage metadata
    chunk_count = Column(Integer, default=0)
    qdrant_collection = Column(String(100), default="documents")
    qdrant_point_ids = Column(JSON)  # List of point IDs in Qdrant

    # Stats
    requirement_count = Column(Integer, default=0)
    test_case_count = Column(Integer, default=0)  # Test cases generated from this doc

    # Additional metadata
    doc_metadata = Column(JSON)  # Flexible storage for source-specific data
