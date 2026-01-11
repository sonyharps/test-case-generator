import httpx
from typing import List, Union
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using Ollama

    Uses 'nomic-embed-text' model (768 dimensions)
    Free, local, good quality for semantic search
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL if hasattr(settings, 'OLLAMA_BASE_URL') else "http://localhost:11434"
        self.model = "nomic-embed-text"
        self.dimension = 768

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for single text

        Args:
            text: Input text

        Returns:
            Embedding vector (768 dimensions)
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch)

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        embeddings = []

        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                try:
                    response = await client.post(
                        f"{self.base_url}/api/embed",
                        json={
                            "model": self.model,
                            "input": text
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    # Ollama returns "embeddings" (plural) as an array
                    embeddings.append(data["embeddings"][0])

                except httpx.HTTPError as e:
                    logger.error(
                        f"Failed to generate embedding: {e}",
                        text_preview=text[:100]
                    )
                    # Return zero vector as fallback
                    embeddings.append([0.0] * self.dimension)

        logger.info(f"Generated {len(embeddings)} embeddings", count=len(embeddings))
        return embeddings

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for search query

        (Same as generate_embedding, but semantically clearer for search use case)
        """
        return await self.generate_embedding(query)

    async def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Generate embeddings for documents to be stored

        (Same as generate_embeddings, but semantically clearer for indexing use case)
        """
        return await self.generate_embeddings(documents)


# Singleton instance
embedding_service = EmbeddingService()
