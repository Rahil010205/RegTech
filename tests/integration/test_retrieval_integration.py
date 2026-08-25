"""Retrieval integration tests using PostgreSQL/pgvector."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.retrieval.query_embedding import QueryEmbeddingService
from app.retrieval.retriever import Retriever
from app.retrieval.schemas import RetrievalFilters
from tests.integration.conftest import unit_vector


class _DeterministicQueryEmbedder(QueryEmbeddingService):
    def __init__(self, vector: list[float]) -> None:
        self._vector = vector

    def embed_query(self, query: str) -> list[float]:
        return self._vector


@pytest.mark.integration
def test_basic_retrieval_returns_relevant_clause(db_session: Session, seeded_clauses: dict[str, Any]) -> None:
    retriever = Retriever(
        db_session,
        query_embedder=_DeterministicQueryEmbedder(unit_vector(0)),
    )
    response = retriever.retrieve(
        "What are the requirements for customer data retention?",
        top_k=5,
        filters=RetrievalFilters(document_id=seeded_clauses["version_id"]),
    )

    assert response.total_results >= 1
    assert response.results[0].clause_id == seeded_clauses["retention_clause_id"]
    assert "retain customer records" in response.results[0].text.lower()
    assert response.results[0].similarity == pytest.approx(1.0, abs=1e-6)


@pytest.mark.integration
def test_top_k_limits_results(db_session: Session, seeded_clauses: dict[str, Any]) -> None:
    retriever = Retriever(
        db_session,
        query_embedder=_DeterministicQueryEmbedder(unit_vector(0)),
    )
    response = retriever.retrieve("retention", top_k=1)
    assert response.total_results == 1


@pytest.mark.integration
def test_min_similarity_filters_weak_matches(db_session: Session, seeded_clauses: dict[str, Any]) -> None:
    retriever = Retriever(
        db_session,
        query_embedder=_DeterministicQueryEmbedder(unit_vector(2)),
    )
    response = retriever.retrieve("unrelated topic", top_k=5, min_similarity=0.99)
    assert response.total_results == 0


@pytest.mark.integration
def test_regulator_filter(db_session: Session, seeded_clauses: dict[str, Any]) -> None:
    retriever = Retriever(
        db_session,
        query_embedder=_DeterministicQueryEmbedder(unit_vector(0)),
    )
    response = retriever.retrieve(
        "retention",
        top_k=5,
        filters=RetrievalFilters(regulator=seeded_clauses["regulator"]),
    )
    assert response.total_results >= 1
    assert all(result.regulator == seeded_clauses["regulator"] for result in response.results)

    other_regulator_response = retriever.retrieve(
        "retention",
        top_k=5,
        filters=RetrievalFilters(regulator="ZZZZ"),
    )
    assert other_regulator_response.total_results == 0


@pytest.mark.integration
def test_no_documents_returns_empty_set(db_session: Session) -> None:
    retriever = Retriever(
        db_session,
        query_embedder=_DeterministicQueryEmbedder(unit_vector(0)),
    )
    response = retriever.retrieve(
        "data retention",
        top_k=5,
        filters=RetrievalFilters(document_id=uuid4()),
    )
    assert response.total_results == 0


@pytest.mark.integration
def test_vector_index_exists(db_session: Session) -> None:
    row = db_session.execute(
        text(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'clauses'
              AND indexname = 'ix_clauses_embedding_hnsw'
            """
        )
    ).one_or_none()
    assert row is not None
