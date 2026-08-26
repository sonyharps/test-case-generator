"""
Exemplar Service — "learn from history" for test-case generation.

Two responsibilities:
1. INDEX: after each generation, embed the produced test cases and upsert
   them into the Qdrant `test_cases` collection (deterministic point IDs so
   re-indexing the same session is idempotent).
2. RETRIEVE: before a generation, fetch the most similar historical test
   cases (same user) to inject into the category prompts as style/depth
   reference examples — with strict anti-duplication instructions enforced
   by the prompt builder.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging_config import get_logger
from app.services.embedding_service import embedding_service
from app.services.vector_store_service import vector_store

logger = get_logger(__name__)

# Keep embedded/stored text compact — enough signal for similarity search.
_MAX_TC_CHARS = 1200


def _format_tc_text(tc: Dict[str, Any]) -> str:
    """Render a test case into the canonical text used for embedding + storage."""
    steps = " | ".join(str(s) for s in (tc.get("steps") or [])[:6])
    expected = " | ".join(str(e) for e in (tc.get("expected_result") or [])[:6])
    parts = [
        f"Title: {tc.get('title', '')}",
        f"Module: {tc.get('module', '')}",
        f"Preconditions: {'; '.join(str(p) for p in (tc.get('preconditions') or [])[:3])}",
        f"Steps: {steps}",
        f"Expected: {expected}",
    ]
    return "\n".join(parts)[:_MAX_TC_CHARS]


class ExemplarService:
    """Store & retrieve generated test cases for exemplar-based learning."""

    async def store_generated_test_cases(
        self,
        session_id: str,
        user_id: int,
        requirement: str,
        tcs_by_category: Dict[str, List[Dict[str, Any]]],
    ) -> int:
        """Index generated test cases into Qdrant (idempotent per session).

        Args:
            session_id: Orchestrator session UUID.
            user_id: Owner — retrieval is filtered by this.
            requirement: Originating requirement text (payload metadata).
            tcs_by_category: {"functional": [...], "negative": [...], "boundary": [...]}

        Returns:
            Number of points upserted.
        """
        texts, metadatas = [], []
        for cat, tcs in tcs_by_category.items():
            for tc in tcs or []:
                if not isinstance(tc, dict) or not tc.get("title"):
                    continue
                texts.append(_format_tc_text(tc))
                # Deterministic ID → re-indexing a session overwrites cleanly
                point_key = uuid.uuid5(uuid.NAMESPACE_URL, f"{session_id}:{tc.get('tc_id', '')}")
                metadatas.append({
                    "_point_id": str(point_key),
                    "session_id": session_id,
                    "user_id": user_id,
                    "requirement": (requirement or "")[:300],
                    "tc_type": cat,
                    "tc_id": tc.get("tc_id", ""),
                    "source_type": "generated",
                    "created_at": datetime.utcnow().isoformat(),
                })

        if not texts:
            return 0

        embeddings = await embedding_service.generate_embeddings(texts)
        if not embeddings or len(embeddings) != len(texts):
            logger.warning("exemplar_index_skipped", reason="embedding_failed", count=len(texts))
            return 0

        from qdrant_client.models import PointStruct
        points = [
            PointStruct(
                id=meta.pop("_point_id"),
                vector=emb,
                payload={"text": text, **meta},
            )
            for text, emb, meta in zip(texts, embeddings, metadatas)
        ]
        # Qdrant handles large upserts; chunk to keep requests modest
        for i in range(0, len(points), 100):
            vector_store.client.upsert(collection_name="test_cases", points=points[i : i + 100])

        logger.info("exemplar_indexed", session_id=session_id, user_id=user_id, count=len(points))
        return len(points)

    async def retrieve_exemplars(
        self,
        query_text: str,
        user_id: Optional[int] = None,
        k: int = 8,
        min_score: float = 0.55,
    ) -> List[str]:
        """Fetch the most similar historical test cases, formatted for prompt injection.

        Args:
            query_text: Requirement + document excerpt (the similarity query).
            user_id: Restrict history to this user (privacy: prompts go to cloud LLMs).
            k: Max exemplars returned.
            min_score: Cosine similarity floor — avoid weak matches.

        Returns:
            List of compact exemplar strings (title + steps + expected).
        """
        try:
            query_emb = await embedding_service.embed_query(query_text[:6000])
        except Exception as e:
            logger.warning("exemplar_embed_failed", error=str(e))
            return []

        filt = {"user_id": user_id, "source_type": "generated"} if user_id else {"source_type": "generated"}
        hits = await vector_store.search_similar(
            collection_name="test_cases",
            query_embedding=query_emb,
            limit=k * 2,  # over-fetch → dedupe by title
            filter_dict=filt,
            score_threshold=min_score,
        )

        seen_titles = set()
        exemplars = []
        for hit in hits:
            text = hit.get("text", "")
            title = text.split("\n")[0].replace("Title: ", "").strip().lower()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            exemplars.append(self._compact(text))
            if len(exemplars) >= k:
                break

        logger.info(
            "exemplar_retrieved",
            user_id=user_id,
            hits=len(hits),
            exemplars=len(exemplars),
            top_score=round(hits[0]["score"], 3) if hits else None,
        )
        return exemplars

    @staticmethod
    def _compact(tc_text: str, max_chars: int = 420) -> str:
        """Trim a stored TC text to a prompt-friendly exemplar."""
        lines = [l for l in tc_text.split("\n") if l.strip()]
        # Keep Title, Steps, Expected — drop Preconditions for brevity
        keep = [l for l in lines if not l.startswith("Preconditions:")]
        out = "\n".join(keep)
        return out[:max_chars]


# Singleton
exemplar_service = ExemplarService()
