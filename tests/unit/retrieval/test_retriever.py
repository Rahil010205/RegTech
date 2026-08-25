"""Unit tests for Retriever orchestration."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.retrieval.query_embedding import QueryEmbeddingService
from app.retrieval.retriever import Retriever
from app.retrieval.schemas import RetrievalFilters
from app.retrieval.vector_search import VectorSearchRow, VectorSearchService


class _FakeQueryEmbedder(QueryEmbeddingService):
    def __init__(self) -> None:
        pass

    def embed_query(self, query: str) -> list[float]:
        return [0.0] * 1023 + [1.0]


class TestRetriever:
    def setup_method(self) -> None:
        self.session = MagicMock()
        self.vector_search = MagicMock(spec=VectorSearchService)
        self.retriever = Retriever(
            self.session,
            query_embedder=_FakeQueryEmbedder(),
            vector_search=self.vector_search,
        )

    def test_retrieve_returns_top_results(self) -> None:
        clause_id = uuid4()
        document_id = uuid4()
        self.vector_search.search.return_value = [
            VectorSearchRow(
                clause_id=clause_id,
                document_id=document_id,
                document_name="RBI Data Retention",
                regulator="RBI",
                clause_number="4.1",
                section="Data Retention",
                text="retain customer records",
                page_number=18,
                metadata={},
                similarity=0.9123,
            )
        ]

        response = self.retriever.retrieve(
            "What are the customer data retention requirements?",
            top_k=5,
        )

        assert response.total_results == 1
        assert response.results[0].clause_id == clause_id
        assert response.results[0].similarity == 0.9123
        self.vector_search.search.assert_called_once()

    def test_empty_query_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self.retriever.retrieve("   ")

    def test_top_k_limit_enforced(self) -> None:
        with pytest.raises(ValidationError):
            self.retriever.retrieve("valid query", top_k=100)

    def test_min_similarity_validation(self) -> None:
        with pytest.raises(ValidationError):
            self.retriever.retrieve("valid query", min_similarity=1.5)

    def test_passes_filters_to_vector_search(self) -> None:
        self.vector_search.search.return_value = []
        filters = RetrievalFilters(regulator="RBI", jurisdiction="IN")
        self.retriever.retrieve("security controls", top_k=3, filters=filters)
        _, kwargs = self.vector_search.search.call_args
        assert kwargs["filters"].regulator == "RBI"

    def test_no_results_returns_empty_response(self) -> None:
        self.vector_search.search.return_value = []
        response = self.retriever.retrieve("unknown topic xyz")
        assert response.total_results == 0
        assert response.results == []
