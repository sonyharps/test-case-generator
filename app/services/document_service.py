from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, BinaryIO
from pathlib import Path
import shutil
import os

from app.models.document import UploadedDocument, DocumentType, ProcessingStatus
from app.services.document_processing import document_processor, DocumentType as ProcDocType
from app.services.embedding_service import embedding_service
from app.services.vector_store_service import vector_store
from app.services.pubsub_service import pubsub_service
from app.core.logging_config import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class DocumentService:
    """Service for managing document uploads and processing"""

    UPLOAD_DIR = Path("data/uploads")

    def __init__(self):
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    async def upload_document(
        self,
        user_id: int,
        file: BinaryIO,
        filename: str,
        db: AsyncSession
    ) -> UploadedDocument:
        """
        Upload and save document file

        Args:
            user_id: User ID
            file: File object
            filename: Original filename
            db: Database session

        Returns:
            Created document record
        """
        # Determine file type
        extension = Path(filename).suffix.lower().lstrip(".")
        try:
            file_type = DocumentType(extension)
        except ValueError:
            raise ValueError(f"Unsupported file type: {extension}")

        # Save file to disk
        user_dir = self.UPLOAD_DIR / str(user_id)
        user_dir.mkdir(exist_ok=True)

        file_path = user_dir / filename
        file_size = 0

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file, f)
            file_size = f.tell()

        logger.info(
            f"Saved uploaded file: {filename}",
            user_id=user_id,
            file_size=file_size,
            file_type=extension
        )

        # Create database record
        document = UploadedDocument(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            file_path=str(file_path),
            processing_status=ProcessingStatus.PENDING
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        logger.info(f"Created document record", document_id=document.id)

        return document

    async def process_document(
        self,
        document_id: int,
        user_id: int,
        db: AsyncSession,
        extract_requirements: bool = True
    ) -> UploadedDocument:
        """
        Process uploaded document:
        1. Parse PDF/Word
        2. Extract requirements (optional)
        3. Chunk text
        4. Generate embeddings
        5. Store in Qdrant

        Args:
            document_id: Document ID
            user_id: User ID
            db: Database session
            extract_requirements: Whether to extract requirements using LLM

        Returns:
            Updated document with processing results
        """
        # Get document
        result = await db.execute(
            select(UploadedDocument).where(
                UploadedDocument.id == document_id,
                UploadedDocument.user_id == user_id
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # Update status
        document.processing_status = ProcessingStatus.PROCESSING
        await db.commit()

        # Publish processing started event
        pubsub_service.publish_document_update(
            user_id=user_id,
            document_id=document_id,
            status="processing",
            data={"filename": document.filename}
        )

        try:
            # Map DocumentType to ProcDocType
            proc_doc_type = ProcDocType(document.file_type.value)

            # Process document using framework
            result = await document_processor.process_document(
                doc_type=proc_doc_type,
                source_id=document.file_path,
                extract_requirements=extract_requirements
            )

            parsed_doc = result["parsed_doc"]
            requirements = result["requirements"]
            chunks = result["chunks"]

            # Update document with parsed data
            document.title = parsed_doc.title
            document.full_text = parsed_doc.full_text
            document.content_preview = parsed_doc.full_text[:500]
            document.sections = [
                {"heading": sec["heading"], "content": sec["content"]}
                for sec in parsed_doc.sections
            ]

            if requirements:
                document.extracted_requirements = [
                    {
                        "title": req.title,
                        "description": req.description,
                        "section": req.section,
                        "acceptance_criteria": req.acceptance_criteria,
                        "priority": req.priority,
                        "tags": req.tags
                    }
                    for req in requirements
                ]
                document.requirement_count = len(requirements)

            # Generate embeddings for chunks
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = await embedding_service.embed_documents(chunk_texts)

            # Store in Qdrant
            metadata_list = [
                {
                    "document_id": document.id,
                    "user_id": user_id,
                    "filename": document.filename,
                    "title": document.title,
                    "chunk_index": chunk.chunk_index,
                    "source_type": "document"
                }
                for chunk in chunks
            ]

            point_ids = await vector_store.store_chunks(
                collection_name="documents",
                chunks=chunk_texts,
                embeddings=embeddings,
                metadata=metadata_list
            )

            # Update document with vector storage info
            document.chunk_count = len(chunks)
            document.qdrant_point_ids = point_ids
            document.processing_status = ProcessingStatus.COMPLETED

            await db.commit()
            await db.refresh(document)

            logger.info(
                f"Document processed successfully",
                document_id=document.id,
                chunks=len(chunks),
                requirements=len(requirements)
            )

            # Publish completed event
            pubsub_service.publish_document_update(
                user_id=user_id,
                document_id=document.id,
                status="completed",
                data={
                    "filename": document.filename,
                    "title": document.title,
                    "chunk_count": document.chunk_count,
                    "requirement_count": document.requirement_count
                }
            )

            return document

        except Exception as e:
            logger.error(
                f"Document processing failed: {e}",
                document_id=document_id,
                exc_info=True
            )

            document.processing_status = ProcessingStatus.FAILED
            document.error_message = str(e)
            await db.commit()

            # Publish failed event
            pubsub_service.publish_document_update(
                user_id=user_id,
                document_id=document_id,
                status="failed",
                data={
                    "filename": document.filename,
                    "error": str(e)
                }
            )

            raise

    async def list_documents(
        self,
        user_id: int,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status: Optional[ProcessingStatus] = None
    ):
        """List user's documents"""
        # Build base query
        base_where = [UploadedDocument.user_id == user_id]
        if status:
            base_where.append(UploadedDocument.processing_status == status)

        # Get total count
        count_query = select(func.count(UploadedDocument.id)).where(*base_where)
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get documents with raw SQL (casting enums to text to avoid async issues)
        from sqlalchemy import text
        raw_sql = text("""
            SELECT id, filename, title, file_type::text as file_type,
                   content_preview, requirement_count, test_case_count,
                   processing_status::text as processing_status,
                   created_at, updated_at
            FROM uploaded_documents
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """)
        result = await db.execute(raw_sql, {"user_id": user_id, "limit": limit, "skip": skip})
        documents = result.all()

        # Convert to dicts
        documents_data = []
        for row in documents:
            documents_data.append({
                "id": row.id,
                "filename": row.filename,
                "file_type": row.file_type,
                "title": row.title or row.filename,
                "content_preview": row.content_preview or "",
                "processing_status": row.processing_status,
                "requirement_count": row.requirement_count or 0,
                "test_case_count": row.test_case_count or 0,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            })

        return {
            "documents": documents_data,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    async def get_document(
        self,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> UploadedDocument:
        """Get document by ID"""
        result = await db.execute(
            select(UploadedDocument).where(
                UploadedDocument.id == document_id,
                UploadedDocument.user_id == user_id
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError(f"Document not found: {document_id}")

        return document

    async def delete_document(
        self,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ):
        """Delete document and associated data"""
        document = await self.get_document(document_id, user_id, db)

        # Delete from Qdrant
        if document.qdrant_point_ids:
            await vector_store.delete_by_metadata(
                collection_name="documents",
                filter_dict={"document_id": document_id}
            )

        # Delete file from disk
        if document.file_path and os.path.exists(document.file_path):
            os.remove(document.file_path)

        # Delete from database
        await db.delete(document)
        await db.commit()

        logger.info(f"Document deleted", document_id=document_id)

    async def find_similar_documents(
        self,
        query_text: str,
        user_id: int,
        limit: int = 5
    ) -> List[dict]:
        """
        Find similar documents using RAG

        Args:
            query_text: Query text (requirement)
            user_id: User ID
            limit: Max results

        Returns:
            List of similar documents with scores
        """
        # Generate query embedding
        query_embedding = await embedding_service.embed_query(query_text)

        # Search in Qdrant
        results = await vector_store.search_similar(
            collection_name="documents",
            query_embedding=query_embedding,
            limit=limit,
            filter_dict={"user_id": user_id},
            score_threshold=0.5
        )

        return results


# Singleton instance
document_service = DocumentService()
