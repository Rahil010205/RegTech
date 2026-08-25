"""High-level retrieval orchestrator."""

from __future__ import annotations

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import ValidationError
from app.ingestion.embedding_service import EmbeddingService
from app.retrieval.query_embedding import QueryEmbeddingService
from app.retrieval.schemas import RetrievedClause, RetrievalFilters, RetrievalResponse
from app.retrieval.vector_search import VectorSearchService


class Retriever:
    """Retrieve regulatory clauses using query embeddings and pgvector search."""

    def __init__(
        self,
        session: Session,
        *,
        settings: Settings | None = None,
        query_embedder: QueryEmbeddingService | None = None,
        vector_search: VectorSearchService | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.query_embedder = query_embedder or QueryEmbeddingService(EmbeddingService())
        self.vector_search = vector_search or VectorSearchService(session)

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: RetrievalFilters | dict | None = None,
        min_similarity: float | None = None,
    ) -> RetrievalResponse:
        """Retrieve the most relevant regulatory clauses for a natural-language query."""
        normalized_query = query.strip()
        if not normalized_query:
            raise ValidationError("Query cannot be empty")

        effective_top_k = top_k or self.settings.retrieval_top_k
        if effective_top_k < 1 or effective_top_k > self.settings.retrieval_top_k_max:
            raise ValidationError(
                f"top_k must be between 1 and {self.settings.retrieval_top_k_max}",
                details={"top_k": effective_top_k},
            )

        if min_similarity is not None and not 0.0 <= min_similarity <= 1.0:
            raise ValidationError(
                "min_similarity must be between 0.0 and 1.0",
                details={"min_similarity": min_similarity},
            )

        parsed_filters = self._parse_filters(filters)

        logger.info("Retrieval started — query_length={} top_k={}", len(normalized_query), effective_top_k)
        query_embedding = self.query_embedder.embed_query(normalized_query)
        logger.info("Query embedding generated")

        rows = self.vector_search.search(
            query_embedding,
            top_k=effective_top_k,
            filters=parsed_filters,
            min_similarity=min_similarity,
        )

        results = [
            RetrievedClause(
                clause_id=row.clause_id,
                document_id=row.document_id,
                document_name=row.document_name,
                regulator=row.regulator,
                clause_number=row.clause_number,
                section=row.section,
                text=row.text,
                page_number=row.page_number,
                similarity=round(row.similarity, 4),
                metadata=row.metadata,
            )
            for row in rows
        ]

        if results:
            logger.info(
                "Retrieval completed — retrieved {} clause(s), best_similarity={:.4f}",
                len(results),
                results[0].similarity,
            )
        else:
            logger.info("Retrieval completed — no clauses matched the query/filters")

        return RetrievalResponse(
            query=normalized_query,
            top_k=effective_top_k,
            min_similarity=min_similarity,
            results=results,
            total_results=len(results),
        )

    @staticmethod
    def _parse_filters(filters: RetrievalFilters | dict | None) -> RetrievalFilters | None:
        if filters is None:
            return None
        if isinstance(filters, RetrievalFilters):
            return filters
        return RetrievalFilters.model_validate(filters)


def search_clauses(
    session: Session,
    query: str,
    top_k: int | None = None,
    filters: RetrievalFilters | dict | None = None,
    min_similarity: float | None = None,
) -> RetrievalResponse:
    """Functional convenience wrapper around :class:`Retriever`."""
    return Retriever(session).retrieve(
        query=query,
        top_k=top_k,
        filters=filters,
        min_similarity=min_similarity,
    )
