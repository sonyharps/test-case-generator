from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
import uuid
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class VectorStoreService:
    """
    Service for managing vector embeddings in Qdrant

    Collections:
    - documents: Uploaded documents (PRD, user stories, etc.)
    - test_cases: Historical test cases for retrieval
    - requirements: Requirements library
    - best_practices: QA patterns and templates
    """

    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST if hasattr(settings, 'QDRANT_HOST') else "localhost",
            port=settings.QDRANT_PORT if hasattr(settings, 'QDRANT_PORT') else 6333
        )
        # Dimension matches the configured embedding model (Gemini embedding-001 = 3072)
        self.embedding_size = settings.EMBEDDING_DIMENSION
        self._ensure_collections()

    def _ensure_collections(self):
        """Create collections if they don't exist"""
        collections = ["documents", "test_cases", "requirements", "best_practices"]

        existing_collections = [col.name for col in self.client.get_collections().collections]

        for collection in collections:
            if collection not in existing_collections:
                self.client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(
                        size=self.embedding_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {collection}")

    async def store_chunks(
        self,
        collection_name: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Store document chunks with embeddings

        Args:
            collection_name: Target collection
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadata: List of metadata dicts for each chunk

        Returns:
            List of assigned point IDs
        """
        if len(chunks) != len(embeddings) != len(metadata):
            raise ValueError("Chunks, embeddings, and metadata must have same length")

        points = []
        point_ids = []

        for chunk, embedding, meta in zip(chunks, embeddings, metadata):
            point_id = str(uuid.uuid4())
            point_ids.append(point_id)

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk,
                        **meta
                    }
                )
            )

        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

        logger.info(
            f"Stored {len(points)} chunks in collection '{collection_name}'",
            collection=collection_name,
            chunk_count=len(points)
        )

        return point_ids

    async def search_similar(
        self,
        collection_name: str,
        query_embedding: List[float],
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors

        Args:
            collection_name: Collection to search
            query_embedding: Query vector
            limit: Max results to return
            filter_dict: Optional metadata filters (e.g., {"user_id": 123})
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of dicts with 'text', 'score', and metadata
        """
        # Build query parameters for newer Qdrant client API
        query_params = {
            "collection_name": collection_name,
            "query": query_embedding,
            "limit": limit,
            "score_threshold": score_threshold
        }

        if filter_dict:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            conditions = [
                FieldCondition(key=key, match=MatchValue(value=value))
                for key, value in filter_dict.items()
            ]
            query_params["query_filter"] = Filter(must=conditions)

        results = self.client.query_points(**query_params).points

        return [
            {
                "id": hit.id,
                "text": hit.payload.get("text", ""),
                "score": hit.score,
                "metadata": {k: v for k, v in hit.payload.items() if k != "text"}
            }
            for hit in results
        ]

    async def delete_by_metadata(
        self,
        collection_name: str,
        filter_dict: Dict[str, Any]
    ) -> int:
        """
        Delete points matching metadata filter

        Args:
            collection_name: Collection name
            filter_dict: Metadata to match (e.g., {"document_id": 123})

        Returns:
            Number of deleted points
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        conditions = [
            FieldCondition(key=key, match=MatchValue(value=value))
            for key, value in filter_dict.items()
        ]

        result = self.client.delete(
            collection_name=collection_name,
            points_selector=Filter(must=conditions)
        )

        logger.info(
            f"Deleted points from collection '{collection_name}'",
            collection=collection_name,
            filter=filter_dict
        )

        return result

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection statistics"""
        info = self.client.get_collection(collection_name)
        return {
            "name": collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status
        }


# Singleton instance
vector_store = VectorStoreService()
