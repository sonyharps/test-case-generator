from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from sentence_transformers import CrossEncoder
import numpy as np

from app.services.embedding_service import embedding_service
from app.services.vector_store_service import vector_store
from app.pipeline.llm.llm_router import get_llm_client
from app.core.logging_config import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class AdvancedRAGService:
    """
    Advanced RAG with semantic re-ranking, query expansion,
    hybrid search, and citation tracking
    """

    def __init__(self):
        # Cross-encoder for re-ranking (more accurate than bi-encoder)
        # Using a small, fast model that works well for semantic similarity
        self.reranker = None  # Lazy load
        self._reranker_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def _get_reranker(self) -> CrossEncoder:
        """Lazy load cross-encoder model"""
        if self.reranker is None:
            logger.info(f"Loading cross-encoder model: {self._reranker_model}")
            self.reranker = CrossEncoder(self._reranker_model)
            logger.info("Cross-encoder model loaded successfully")
        return self.reranker

    async def expand_query(
        self,
        query: str,
        num_expansions: int = 3
    ) -> List[str]:
        """
        Expand query into multiple variations using LLM

        This improves recall by finding documents that match
        the intent but use different wording.

        Args:
            query: Original query
            num_expansions: Number of query variations to generate

        Returns:
            List of query variations (including original)
        """
        prompt = f"""Generate {num_expansions} alternative phrasings of this requirement
to help search for relevant documents. Keep the core meaning but vary the wording.

Original requirement:
{query}

Output format: JSON array of strings.
Example: ["variation 1", "variation 2", "variation 3"]

ONLY output the JSON array, nothing else."""

        try:
            # Use Ollama client for query expansion
            llm_client = get_llm_client(model="llama3.1:8b")
            response = await llm_client.generate(prompt)

            # Parse JSON response
            import json
            expansions = json.loads(response.strip())

            # Include original query
            all_queries = [query] + expansions

            logger.info(
                f"Query expansion generated {len(expansions)} variations",
                original=query[:50],
                expansions_count=len(expansions)
            )

            return all_queries

        except Exception as e:
            logger.warning(f"Query expansion failed, using original query: {e}")
            return [query]

    async def hybrid_search(
        self,
        query: str,
        collection_name: str,
        user_id: Optional[int] = None,
        top_k: int = 20,
        semantic_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic (dense) and keyword (sparse) search

        Args:
            query: Search query
            collection_name: Qdrant collection to search
            user_id: Optional user filter
            top_k: Number of results to retrieve before fusion
            semantic_weight: Weight for semantic search (0-1), keyword gets (1-weight)

        Returns:
            Fused and scored results
        """
        # 1. Semantic search
        query_embedding = await embedding_service.embed_query(query)
        filter_dict = {"user_id": user_id} if user_id else None

        semantic_results = await vector_store.search_similar(
            collection_name=collection_name,
            query_embedding=query_embedding,
            limit=top_k,
            filter_dict=filter_dict,
            score_threshold=0.3
        )

        # 2. Keyword search (BM25-like) using Qdrant's full-text search
        # For now, we'll use a simplified version - searching by text matching
        # In production, you'd want to add BM25 scoring via Qdrant's payload index
        keyword_results = await self._keyword_search(
            query=query,
            collection_name=collection_name,
            user_id=user_id,
            limit=top_k
        )

        # 3. Reciprocal Rank Fusion (RRF)
        fused_results = self._reciprocal_rank_fusion(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            semantic_weight=semantic_weight
        )

        logger.info(
            f"Hybrid search completed",
            collection=collection_name,
            semantic_count=len(semantic_results),
            keyword_count=len(keyword_results),
            fused_count=len(fused_results)
        )

        return fused_results[:top_k]

    async def _keyword_search(
        self,
        query: str,
        collection_name: str,
        user_id: Optional[int],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Simple keyword-based search

        NOTE: This is a simplified implementation. For production,
        consider using Qdrant's full-text search with BM25 scoring
        or integrate with Elasticsearch.
        """
        # For now, return empty list - keyword search requires additional setup
        # This can be enhanced with Qdrant's payload index or external search engine
        return []

    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        semantic_weight: float = 0.7,
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) to combine rankings

        RRF formula: score = semantic_weight * 1/(k + rank_semantic) +
                            (1-semantic_weight) * 1/(k + rank_keyword)

        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            semantic_weight: Weight for semantic search
            k: Constant to avoid division by zero (typically 60)

        Returns:
            Fused and re-scored results
        """
        scores = {}

        # Add semantic scores
        for rank, result in enumerate(semantic_results, start=1):
            doc_id = result['id']
            rrf_score = semantic_weight / (k + rank)
            scores[doc_id] = {
                'score': rrf_score,
                'data': result,
                'semantic_rank': rank,
                'keyword_rank': None
            }

        # Add keyword scores
        keyword_weight = 1 - semantic_weight
        for rank, result in enumerate(keyword_results, start=1):
            doc_id = result['id']
            rrf_score = keyword_weight / (k + rank)

            if doc_id in scores:
                scores[doc_id]['score'] += rrf_score
                scores[doc_id]['keyword_rank'] = rank
            else:
                scores[doc_id] = {
                    'score': rrf_score,
                    'data': result,
                    'semantic_rank': None,
                    'keyword_rank': rank
                }

        # Sort by fused score
        fused_results = sorted(
            scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )

        # Return with updated scores
        return [
            {
                **item['data'],
                'fusion_score': item['score'],
                'semantic_rank': item['semantic_rank'],
                'keyword_rank': item['keyword_rank']
            }
            for item in fused_results
        ]

    async def semantic_rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Re-rank results using cross-encoder for more accurate scoring

        Cross-encoders are more accurate than bi-encoders (used for initial retrieval)
        because they can attend to both query and document simultaneously.

        Args:
            query: Original query
            results: Initial retrieval results
            top_k: Number of results to return after re-ranking

        Returns:
            Re-ranked results with updated scores
        """
        if not results:
            return []

        # Get cross-encoder model
        reranker = self._get_reranker()

        # Prepare query-document pairs
        pairs = [
            [query, result['text']]
            for result in results
        ]

        # Get cross-encoder scores (run in thread to avoid blocking event loop)
        # This is CPU-intensive and must not block async operations
        scores = await asyncio.to_thread(reranker.predict, pairs)

        # Attach scores to results
        for result, score in zip(results, scores):
            result['rerank_score'] = float(score)
            result['original_score'] = result.get('score', 0.0)

        # Sort by rerank score
        reranked = sorted(
            results,
            key=lambda x: x['rerank_score'],
            reverse=True
        )

        logger.info(
            f"Re-ranked {len(results)} results",
            top_original_score=results[0].get('score', 0) if results else 0,
            top_rerank_score=reranked[0]['rerank_score'] if reranked else 0
        )

        return reranked[:top_k]

    async def retrieve_with_citations(
        self,
        requirement: str,
        user_id: int,
        db: AsyncSession,
        top_k: int = 5,
        use_query_expansion: bool = True,
        use_reranking: bool = True
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Advanced retrieval with query expansion, re-ranking, and citation tracking

        Returns both the retrieved documents and citation metadata.

        Args:
            requirement: Query requirement
            user_id: User ID for filtering
            db: Database session
            top_k: Final number of results to return
            use_query_expansion: Whether to expand queries
            use_reranking: Whether to re-rank with cross-encoder

        Returns:
            Tuple of (retrieved_docs, citation_metadata)
        """
        logger.info(
            f"Advanced RAG retrieval started",
            query_expansion=use_query_expansion,
            reranking=use_reranking,
            top_k=top_k
        )

        # 1. Query expansion (optional)
        queries = [requirement]
        if use_query_expansion:
            queries = await self.expand_query(requirement, num_expansions=2)

        # 2. Retrieve from multiple collections with expanded queries
        all_results = {}
        collections = ["documents", "test_cases", "requirements"]

        for collection in collections:
            collection_results = []

            # Search with each query variation
            for query in queries:
                results = await self.hybrid_search(
                    query=query,
                    collection_name=collection,
                    user_id=user_id,
                    top_k=top_k * 2,  # Get more for re-ranking
                    semantic_weight=0.7
                )
                collection_results.extend(results)

            # Deduplicate by ID
            seen_ids = set()
            unique_results = []
            for result in collection_results:
                if result['id'] not in seen_ids:
                    seen_ids.add(result['id'])
                    unique_results.append(result)

            all_results[collection] = unique_results[:top_k * 2]

        # 3. Re-rank results (optional)
        if use_reranking:
            for collection in collections:
                if all_results[collection]:
                    all_results[collection] = await self.semantic_rerank(
                        query=requirement,
                        results=all_results[collection],
                        top_k=top_k
                    )
        else:
            # Just take top_k without re-ranking
            for collection in collections:
                all_results[collection] = all_results[collection][:top_k]

        # 4. Build citation metadata
        citation_metadata = {
            "query_variations": queries,
            "collections_searched": collections,
            "total_results": sum(len(v) for v in all_results.values()),
            "citations_by_collection": {
                collection: [
                    {
                        "id": r['id'],
                        "text": r['text'][:200] + "...",
                        "score": r.get('rerank_score', r.get('fusion_score', r.get('score', 0))),
                        "metadata": r.get('metadata', {})
                    }
                    for r in results
                ]
                for collection, results in all_results.items()
            },
            "retrieval_config": {
                "query_expansion": use_query_expansion,
                "reranking": use_reranking,
                "top_k": top_k
            }
        }

        # 5. Flatten all results for consumption
        all_docs = []
        for collection, results in all_results.items():
            for result in results:
                result['source_collection'] = collection
                all_docs.append(result)

        # Sort by best score
        all_docs.sort(
            key=lambda x: x.get('rerank_score', x.get('fusion_score', x.get('score', 0))),
            reverse=True
        )

        logger.info(
            f"Advanced RAG retrieval completed",
            total_docs=len(all_docs),
            queries_used=len(queries),
            top_score=all_docs[0].get('rerank_score', 0) if all_docs else 0
        )

        return all_docs[:top_k * len(collections)], citation_metadata


# Singleton instance
advanced_rag_service = AdvancedRAGService()
