from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from app.models.document import ProcessingStatus
from app.services.document_service import document_service
from app.services.pubsub_service import pubsub_service
from app.schemas.document_schema import (
    DocumentUploadResponse,
    DocumentProcessingResult,
    DocumentSummary,
    DocumentDetail,
    DocumentListResponse,
    SimilarDocumentResult
)
from app.core.logging_config import get_logger
from app.core.config import settings

router = APIRouter()
logger = get_logger(__name__)


async def _process_document_background(document_id: int, user_id: int, extract_requirements: bool = True):
    """
    Background task to process document with its own DB session

    This creates a new database session to avoid using the closed session from the request
    """
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            await document_service.process_document(
                document_id=document_id,
                user_id=user_id,
                db=db,
                extract_requirements=extract_requirements
            )
        except Exception as e:
            logger.error(f"Background document processing failed: {e}", exc_info=True)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    process_immediately: bool = Query(True, description="Process document immediately after upload"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document (PDF, Word, Markdown, Text)

    The document will be saved and optionally processed immediately.
    Processing includes:
    - Text extraction
    - Requirement extraction (using LLM)
    - Chunking and embedding generation
    - Storage in vector database

    Max file size: 50MB
    """
    logger.info(
        f"Document upload request",
        user_id=current_user.id,
        filename=file.filename,
        content_type=file.content_type
    )

    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to start

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    # Upload document
    try:
        document = await document_service.upload_document(
            user_id=current_user.id,
            file=file.file,
            filename=file.filename,
            db=db
        )

        # Process in background if requested
        if process_immediately:
            # Process in background to avoid blocking the request
            # Note: Create a new DB session in the background task
            background_tasks.add_task(
                _process_document_background,
                document.id,
                current_user.id,
                extract_requirements=True
            )
            message = "Document uploaded and queued for processing"
        else:
            message = "Document uploaded successfully"

        return DocumentUploadResponse(
            document_id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            processing_status=document.processing_status,
            message=message
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Upload failed")


@router.post("/{document_id}/process", response_model=DocumentProcessingResult)
async def process_document(
    document_id: int,
    extract_requirements: bool = Query(True, description="Extract requirements using LLM"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process an uploaded document

    Extracts text, identifies requirements, generates embeddings
    """
    logger.info(f"Process document request", document_id=document_id, user_id=current_user.id)

    try:
        document = await document_service.process_document(
            document_id=document_id,
            user_id=current_user.id,
            db=db,
            extract_requirements=extract_requirements
        )

        requirements = []
        if document.extracted_requirements:
            from app.schemas.document_schema import RequirementExtract
            requirements = [RequirementExtract(**req) for req in document.extracted_requirements]

        return DocumentProcessingResult(
            document_id=document.id,
            title=document.title or document.filename,
            sections=document.sections or [],
            requirements=requirements,
            chunk_count=document.chunk_count,
            processing_status=document.processing_status,
            error_message=document.error_message
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Document processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Processing failed")


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ProcessingStatus] = Query(None, description="Filter by processing status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's uploaded documents

    Supports pagination and filtering by processing status
    """
    logger.info(f"List documents", user_id=current_user.id, skip=skip, limit=limit)

    result = await document_service.list_documents(
        user_id=current_user.id,
        db=db,
        skip=skip,
        limit=limit,
        status=status
    )

    return DocumentListResponse(**result)


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a document

    Includes full text, sections, and extracted requirements
    """
    try:
        document = await document_service.get_document(
            document_id=document_id,
            user_id=current_user.id,
            db=db
        )

        return DocumentDetail.from_orm(document)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document

    Removes document file, database record, and vector embeddings
    """
    logger.info(f"Delete document request", document_id=document_id, user_id=current_user.id)

    try:
        await document_service.delete_document(
            document_id=document_id,
            user_id=current_user.id,
            db=db
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/similar/search", response_model=list[SimilarDocumentResult])
async def find_similar_documents(
    query: str = Query(..., description="Search query (requirement text)"),
    limit: int = Query(5, ge=1, le=20, description="Max results"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Find similar documents using RAG semantic search

    Given a requirement text, finds similar documents that might have
    relevant test cases or requirements

    Useful for:
    - Finding reusable test cases
    - Discovering similar requirements
    - Getting context for new requirements
    """
    logger.info(f"Similar document search", user_id=current_user.id, query=query[:100])

    results = await document_service.find_similar_documents(
        query_text=query,
        user_id=current_user.id,
        limit=limit
    )

    # Fetch document details
    similar_docs = []
    for result in results:
        doc_id = result["metadata"].get("document_id")
        if doc_id:
            try:
                doc = await document_service.get_document(doc_id, current_user.id, db)
                similar_docs.append(
                    SimilarDocumentResult(
                        document_id=doc.id,
                        filename=doc.filename,
                        title=doc.title or doc.filename,
                        similarity_score=result["score"],
                        content_preview=result["text"][:200]
                    )
                )
            except:
                continue

    return similar_docs


@router.get("/events/stream")
async def stream_document_events(
    token: str = Query(..., description="Access token for authentication"),
    db: AsyncSession = Depends(get_db)
):
    """
    Server-Sent Events (SSE) stream for real-time document updates

    Subscribe to this endpoint to receive real-time notifications when:
    - Document processing starts
    - Document processing completes
    - Document processing fails
    - Requirements are extracted

    Note: Uses query parameter authentication since EventSource doesn't support headers

    Event format:
    data: {"type": "document_update", "document_id": 123, "status": "completed", ...}
    """
    # Authenticate user from query parameter token
    from app.core.security import verify_token
    from app.models.user import User as UserModel
    from sqlalchemy import select

    try:
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # Fetch user from database
        result = await db.execute(select(UserModel).where(UserModel.id == int(user_id)))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    except Exception as e:
        logger.error(f"SSE authentication failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    return StreamingResponse(
        pubsub_service.subscribe_to_user_events(user.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
