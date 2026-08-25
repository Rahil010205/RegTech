"""Unit tests for query embedding service."""

import pytest

from app.ingestion.embedding_service import EmbeddingService
from app.retrieval.query_embedding import QueryEmbeddingService


class _FakeEmbeddingService(EmbeddingService):
    def __init__(self) -> None:
        pass

    def embed_query(self, query: str) -> list[float]:
        return [float(len(query)), 0.25, 0.5, 0.75]

    @property
    def embedding_dimension(self) -> int:
        return 4


class TestQueryEmbeddingService:
    def test_embed_query_returns_vector(self) -> None:
        service = QueryEmbeddingService(_FakeEmbeddingService())
        vector = service.embed_query("data retention requirements")
        assert vector == [27.0, 0.25, 0.5, 0.75]

    def test_empty_query_rejected(self) -> None:
        service = QueryEmbeddingService(_FakeEmbeddingService())
        with pytest.raises(ValueError):
            service.embed_query("   ")
