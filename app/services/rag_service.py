from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.embedding_service import embedding_service
from app.services.vector_store_service import vector_store
from app.models.document import UploadedDocument
from app.models.session import OrchestratorSession
from app.models.test_case import TestCaseRecord
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation Service

    Provides context-aware retrieval for test case generation:
    - Similar documents and requirements
    - Historical test cases
    - Best practice templates
    """

    async def retrieve_context_for_generation(
        self,
        requirement: str,
        user_id: int,
        db: AsyncSession,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context for test case generation

        Searches across:
        1. User's uploaded documents
        2. Historical test cases
        3. Requirements library
        4. Best practices

        Args:
            requirement: Requirement text
            user_id: User ID
            db: Database session
            top_k: Number of results per category

        Returns:
            Dict with retrieved context organized by category
        """
        logger.info(
            f"Retrieving RAG context for requirement",
            user_id=user_id,
            requirement_preview=requirement[:100]
        )

        # Generate embedding for requirement
        query_embedding = await embedding_service.embed_query(requirement)

        # Search in documents collection
        similar_docs = await vector_store.search_similar(
            collection_name="documents",
            query_embedding=query_embedding,
            limit=top_k,
            filter_dict={"user_id": user_id},
            score_threshold=0.5
        )

        # Search in test_cases collection
        similar_test_cases = await vector_store.search_similar(
            collection_name="test_cases",
            query_embedding=query_embedding,
            limit=top_k,
            filter_dict={"user_id": user_id},
            score_threshold=0.5
        )

        # Search in requirements collection
        similar_requirements = await vector_store.search_similar(
            collection_name="requirements",
            query_embedding=query_embedding,
            limit=top_k,
            filter_dict={"user_id": user_id},
            score_threshold=0.5
        )

        # Search in best_practices collection (no user filter - shared knowledge)
        best_practices = await vector_store.search_similar(
            collection_name="best_practices",
            query_embedding=query_embedding,
            limit=3,
            score_threshold=0.6
        )

        logger.info(
            f"Retrieved RAG context",
            documents=len(similar_docs),
            test_cases=len(similar_test_cases),
            requirements=len(similar_requirements),
            best_practices=len(best_practices)
        )

        return {
            "similar_documents": similar_docs,
            "similar_test_cases": similar_test_cases,
            "similar_requirements": similar_requirements,
            "best_practices": best_practices
        }

    def build_augmented_prompt(
        self,
        requirement: str,
        context: Dict[str, Any],
        test_type: str = "functional",
        base_prompt: Optional[str] = None
    ) -> str:
        """
        Build augmented prompt with retrieved context

        Injects similar examples as few-shot learning

        Args:
            requirement: User's requirement
            context: Retrieved context from retrieve_context_for_generation()
            test_type: Type of test cases to generate
            base_prompt: Optional base prompt to augment (if not provided, creates new prompt)

        Returns:
            Enhanced prompt with context
        """
        prompt_parts = []

        # Add RAG context header
        prompt_parts.append("# RAG Context - Use these as examples and guidance:\n")

        # Add similar documents context
        if context.get("similar_documents"):
            prompt_parts.append("\n## Similar Requirements from Documents:\n")
            for i, doc in enumerate(context["similar_documents"][:2], 1):
                prompt_parts.append(
                    f"{i}. {doc['metadata'].get('title', 'Untitled')}\n"
                    f"   Content: {doc['text'][:200]}...\n"
                    f"   (Similarity: {doc['score']:.2f})\n"
                )

        # Add similar test cases as examples
        if context.get("similar_test_cases"):
            prompt_parts.append("\n## Example Test Cases (for reference):\n")
            for i, tc in enumerate(context["similar_test_cases"][:2], 1):
                prompt_parts.append(
                    f"{i}. {tc['text'][:300]}...\n"
                    f"   (Similarity: {tc['score']:.2f})\n"
                )

        # Add best practices
        if context.get("best_practices"):
            prompt_parts.append("\n## Best Practices to Follow:\n")
            for i, bp in enumerate(context["best_practices"], 1):
                prompt_parts.append(f"{i}. {bp['text']}\n")

        # Build context text
        context_text = "\n".join(prompt_parts)

        # If base_prompt provided, prepend context to it
        if base_prompt:
            augmented_prompt = f"""{context_text}

---

# Your Task:
Use the examples and best practices above as reference, but create new test cases specific to this requirement.

{base_prompt}
"""
        else:
            # Fallback: create prompt from scratch
            augmented_prompt = f"""
{context_text}

## Your Task:
Generate {test_type} test cases for the following requirement:

**Requirement:**
{requirement}

Use the examples and best practices above as reference, but create new test cases specific to this requirement.

Output format: JSON array of test cases.
"""

        return augmented_prompt

    async def store_generated_test_cases(
        self,
        session_id: str,
        test_cases: List[Dict[str, Any]],
        requirement: str,
        user_id: int
    ):
        """
        Store generated test cases in vector DB for future retrieval

        Args:
            session_id: Orchestrator session ID
            test_cases: Generated test cases
            requirement: Original requirement
            user_id: User ID
        """
        chunks = []
        embeddings_list = []
        metadata_list = []

        for tc in test_cases:
            # Build text representation of test case
            tc_text = f"""
Title: {tc.get('title', 'Untitled')}
Preconditions: {', '.join(tc.get('preconditions', []))}
Steps: {', '.join(tc.get('steps', []))}
Expected Result: {', '.join(tc.get('expected_result', []))}
"""
            chunks.append(tc_text)

            metadata_list.append({
                "session_id": session_id,
                "user_id": user_id,
                "requirement": requirement[:200],
                "tc_type": tc.get("tc_type", "functional"),
                "tc_id": tc.get("tc_id"),
                "source_type": "generated_test_case"
            })

        # Generate embeddings
        embeddings_list = await embedding_service.embed_documents(chunks)

        # Store in Qdrant
        await vector_store.store_chunks(
            collection_name="test_cases",
            chunks=chunks,
            embeddings=embeddings_list,
            metadata=metadata_list
        )

        logger.info(
            f"Stored generated test cases in vector DB",
            session_id=session_id,
            count=len(test_cases)
        )


# Singleton instance
rag_service = RAGService()
