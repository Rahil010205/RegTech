"""Query embedding generation for retrieval."""

from __future__ import annotations

from loguru import logger

from app.ingestion.embedding_service import EmbeddingService


class QueryEmbeddingService:
    """Generate query embeddings compatible with ingested clause vectors."""

    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self._embedding_service = embedding_service or EmbeddingService()

    def embed_query(self, query: str) -> list[float]:
        """Return a query embedding using the configured ingestion provider."""
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Query cannot be empty")

        logger.debug("Generating query embedding (length={})", len(normalized_query))
        vector = self._embedding_service.embed_query(normalized_query)
        logger.debug("Query embedding generated (dimension={})", len(vector))
        return vector

    @property
    def embedding_dimension(self) -> int:
        return self._embedding_service.embedding_dimension
