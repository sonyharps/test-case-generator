"""
Embedding service using Google Gemini text-embedding-004.

Replaces the previous local Ollama (nomic-embed-text) implementation.
Gemini text-embedding-004 produces 768-dim vectors — the SAME dimensionality
as nomic-embed-text — so existing Qdrant collections (size=768) remain
compatible. Documents still need re-embedding since the vector space differs,
but the collection schema does not need to change.

API docs: https://ai.google.dev/api/embeddings
"""

import asyncio
import httpx
from typing import List
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using Google Gemini (text-embedding-004).

    - Dimension: 768 (matches the previous nomic-embed-text; Qdrant-compatible)
    - Endpoint: generativelanguage.googleapis.com (v1beta)
    - Auth: X-goog-api-key header (GEMINI_API_KEY)
    - Supports batch embedding (up to 100 texts per request)
    """

    # Gemini allows up to 100 inputs per batch request
    _BATCH_SIZE = 100

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.EMBEDDING_MODEL or "text-embedding-004"
        self.dimension = settings.EMBEDDING_DIMENSION or 768
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:batchEmbedContents"
        )
        self.single_endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:embedContent"
        )

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts (<=100) via Gemini batchEmbedContents."""
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key,
        }
        payload = {
            "requests": [
                {
                    "model": f"models/{self.model}",
                    "content": {"parts": [{"text": t}]},
                }
                for t in texts
            ]
        }
        timeout = httpx.Timeout(60.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, verify=True) as client:
            res = await client.post(self.endpoint, json=payload, headers=headers)

            if res.status_code != 200:
                logger.error(
                    "gemini_embedding_error",
                    status_code=res.status_code,
                    response=res.text[:300],
                    batch_size=len(texts),
                )
                raise httpx.HTTPError(
                    f"Gemini embedding API error ({res.status_code}): {res.text[:200]}"
                )

            data = res.json()
            # batchEmbedContents returns {"embeddings": [{"values": [...]}, ...]}
            return [e["values"] for e in data.get("embeddings", [])]

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch).

        Splits into chunks of _BATCH_SIZE to respect the API limit. On failure
        of a batch, falls back to zero-vectors (matching the previous local
        behavior so callers don't crash).

        Args:
            texts: List of input texts.

        Returns:
            List of embedding vectors (768 dimensions each).
        """
        if not texts:
            return []

        all_embeddings: List[List[float]] = []
        # Process in batches to respect Gemini's per-request input limit
        for i in range(0, len(texts), self._BATCH_SIZE):
            batch = texts[i : i + self._BATCH_SIZE]
            try:
                batch_embeddings = await self._embed_batch(batch)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(
                    "embedding_batch_failed",
                    error=str(e),
                    batch_start=i,
                    batch_size=len(batch),
                )
                # Zero-vector fallback (preserves caller-side indexing/shape)
                all_embeddings.extend([[0.0] * self.dimension] * len(batch))

        logger.info("embeddings_generated", count=len(all_embeddings), model=self.model)
        return all_embeddings

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]

    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query (alias for generate_embedding)."""
        return await self.generate_embedding(query)

    async def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Generate embeddings for documents to be indexed (alias for generate_embeddings)."""
        return await self.generate_embeddings(documents)


# Singleton instance
embedding_service = EmbeddingService()
