"""Unit tests for pgvector search service."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.retrieval.schemas import RetrievalFilters
from app.retrieval.vector_search import VectorSearchService


class TestVectorSearchService:
    def test_rejects_wrong_embedding_dimension(self) -> None:
        session = MagicMock()
        service = VectorSearchService(session)
        with pytest.raises(ValueError):
            service.search([0.1, 0.2], top_k=5)

    def test_search_returns_ranked_rows(self) -> None:
        clause_id = uuid4()
        document_id = uuid4()
        session = MagicMock()
        session.execute.return_value.mappings.return_value.all.return_value = [
            {
                "clause_id": clause_id,
                "document_id": document_id,
                "document_name": "RBI Data Retention",
                "regulator": "RBI",
                "clause_number": "4.1",
                "section": "Data Retention",
                "text": "The organization shall retain customer records for seven years.",
                "page_number": 18,
                "metadata": {"regulator": "RBI"},
                "similarity": 0.91,
            }
        ]

        service = VectorSearchService(session)
        vector = [0.0] * 1023 + [1.0]
        results = service.search(
            vector,
            top_k=5,
            filters=RetrievalFilters(regulator="RBI"),
            min_similarity=0.7,
        )

        assert len(results) == 1
        assert results[0].clause_id == clause_id
        assert results[0].similarity == 0.91
        session.execute.assert_called_once()

    def test_database_error_is_wrapped(self) -> None:
        from sqlalchemy.exc import SQLAlchemyError

        from app.core.exceptions import DatabaseError

        session = MagicMock()
        session.execute.side_effect = SQLAlchemyError("boom")
        service = VectorSearchService(session)

        with pytest.raises(DatabaseError):
            service.search([0.0] * 1023 + [1.0], top_k=5)
