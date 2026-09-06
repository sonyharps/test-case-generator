from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    PDF = "pdf"
    WORD = "docx"
    MARKDOWN = "md"
    TEXT = "txt"
    FIGMA = "figma"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    JIRA = "jira"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    document_id: int
    filename: str
    file_type: DocumentType
    file_size: int
    processing_status: ProcessingStatus
    message: str = "Document uploaded successfully"

    class Config:
        from_attributes = True


class RequirementExtract(BaseModel):
    """Extracted requirement from document"""
    title: str
    description: str
    section: Optional[str] = None
    acceptance_criteria: List[str] = []
    priority: Optional[str] = None
    tags: List[str] = []


class DocumentProcessingResult(BaseModel):
    """Result of document processing"""
    document_id: int
    title: str
    sections: List[Dict[str, str]]
    requirements: List[RequirementExtract]
    chunk_count: int
    processing_status: ProcessingStatus
    error_message: Optional[str] = None


class DocumentSummary(BaseModel):
    """Document summary for list view"""
    id: int
    filename: str
    file_type: DocumentType
    title: Optional[str]
    content_preview: Optional[str]
    processing_status: ProcessingStatus
    requirement_count: int
    test_case_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentDetail(BaseModel):
    """Full document details"""
    id: int
    filename: str
    file_type: DocumentType
    file_size: int
    title: Optional[str]
    full_text: Optional[str]
    sections: Optional[List[Dict[str, str]]]
    extracted_requirements: Optional[List[Dict[str, Any]]]
    processing_status: ProcessingStatus
    error_message: Optional[str]
    chunk_count: int
    requirement_count: int
    test_case_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Paginated list of documents"""
    documents: List[DocumentSummary]
    total: int
    skip: int
    limit: int


class GenerateFromDocumentRequest(BaseModel):
    """Request to generate test cases from document"""
    document_id: int
    requirement_indices: Optional[List[int]] = Field(
        None,
        description="Specific requirements to generate from (by index). If None, use all."
    )
    model: str = Field("llama3.1:8b", description="LLM model to use")
    generate_boundary: bool = Field(True, description="Generate boundary test cases")
    include_risk: bool = Field(True, description="Include risk assessment")


class SimilarDocumentResult(BaseModel):
    """Similar document found via RAG"""
    document_id: int
    filename: str
    title: str
    similarity_score: float
    content_preview: str
