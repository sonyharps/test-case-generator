from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from app.services.advanced_rag_service import advanced_rag_service
from app.core.logging_config import get_logger
from pydantic import BaseModel

router = APIRouter()
logger = get_logger(__name__)


class QueryExpansionRequest(BaseModel):
    query: str
    num_expansions: int = 3


class QueryExpansionResponse(BaseModel):
    original_query: str
    expansions: list[str]


class AdvancedRAGRequest(BaseModel):
    requirement: str
    use_query_expansion: bool = True
    use_reranking: bool = True
    top_k: int = 5


class AdvancedRAGResponse(BaseModel):
    results: list[dict]
    citation_metadata: dict
    processing_time_ms: float


@router.post("/query-expansion", response_model=QueryExpansionResponse)
async def expand_query(
    request: QueryExpansionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Demo: Query expansion using LLM

    Generates alternative phrasings of a query to improve recall in search.

    Example:
    - Input: "Login functionality with password reset"
    - Output: ["User authentication with password recovery",
               "Sign-in feature with forgotten password option",
               "Access control with password reset capability"]
    """
    logger.info(
        f"Query expansion request",
        user_id=current_user.id,
        original_query=request.query[:100]
    )

    expansions = await advanced_rag_service.expand_query(
        query=request.query,
        num_expansions=request.num_expansions
    )

    return QueryExpansionResponse(
        original_query=request.query,
        expansions=expansions[1:]  # Exclude original query
    )


@router.post("/advanced-search", response_model=AdvancedRAGResponse)
async def advanced_search(
    request: AdvancedRAGRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Advanced RAG search with:
    - Query expansion (multiple query variations)
    - Hybrid search (semantic + keyword)
    - Semantic re-ranking (cross-encoder)
    - Citation tracking (document sources)

    Returns relevant documents with scores and citations showing
    which documents influenced the results.
    """
    import time
    start_time = time.time()

    logger.info(
        f"Advanced RAG search",
        user_id=current_user.id,
        requirement=request.requirement[:100],
        query_expansion=request.use_query_expansion,
        reranking=request.use_reranking
    )

    try:
        # Retrieve with advanced RAG
        results, citation_metadata = await advanced_rag_service.retrieve_with_citations(
            requirement=request.requirement,
            user_id=current_user.id,
            db=db,
            top_k=request.top_k,
            use_query_expansion=request.use_query_expansion,
            use_reranking=request.use_reranking
        )

        processing_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Advanced RAG search completed",
            results_count=len(results),
            processing_time_ms=processing_time_ms
        )

        return AdvancedRAGResponse(
            results=results,
            citation_metadata=citation_metadata,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Advanced RAG search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advanced RAG search failed: {str(e)}"
        )


@router.post("/rerank")
async def rerank_results(
    query: str,
    results: list[dict],
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user)
):
    """
    Demo: Semantic re-ranking using cross-encoder

    Takes initial search results and re-ranks them using a more
    accurate cross-encoder model that considers query-document pairs.

    More accurate than bi-encoder cosine similarity used in initial retrieval.
    """
    logger.info(
        f"Re-ranking request",
        user_id=current_user.id,
        query=query[:100],
        input_count=len(results)
    )

    # Rerank
    reranked = await advanced_rag_service.semantic_rerank(
        query=query,
        results=results,
        top_k=top_k
    )

    return {
        "query": query,
        "original_count": len(results),
        "reranked_count": len(reranked),
        "results": reranked
    }


@router.get("/hybrid-search")
async def hybrid_search_demo(
    query: str,
    collection: str = Query("documents", description="Collection to search"),
    top_k: int = Query(10, ge=1, le=50),
    semantic_weight: float = Query(0.7, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_active_user)
):
    """
    Demo: Hybrid search combining semantic and keyword search

    Semantic weight controls the balance:
    - 1.0 = Pure semantic (dense vector search)
    - 0.5 = Equal weight semantic + keyword
    - 0.0 = Pure keyword (BM25-like)

    Uses Reciprocal Rank Fusion (RRF) to combine rankings.
    """
    logger.info(
        f"Hybrid search request",
        user_id=current_user.id,
        query=query[:100],
        collection=collection,
        semantic_weight=semantic_weight
    )

    results = await advanced_rag_service.hybrid_search(
        query=query,
        collection_name=collection,
        user_id=current_user.id,
        top_k=top_k,
        semantic_weight=semantic_weight
    )

    return {
        "query": query,
        "collection": collection,
        "semantic_weight": semantic_weight,
        "results_count": len(results),
        "results": results
    }
