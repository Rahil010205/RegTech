"""Real-embedding retrieval quality integration tests."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.retrieval.retriever import Retriever
from app.retrieval.schemas import RetrievalFilters


@pytest.mark.integration
@pytest.mark.slow
def test_real_embeddings_rank_retention_clause_first(
    db_session: Session,
    real_embedded_document: dict[str, Any],
) -> None:
    retriever = Retriever(db_session)
    response = retriever.retrieve(
        "What are the requirements for customer data retention?",
        top_k=5,
        filters=RetrievalFilters(document_id=real_embedded_document["version_id"]),
    )

    assert response.total_results >= 1
    assert any("seven years" in result.text.lower() for result in response.results[:3])
    assert "seven years" in response.results[0].text.lower()
    assert response.results[0].similarity > 0.5


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.parametrize(
    ("query", "expected_snippet"),
    [
        (
            "What are the requirements for customer data retention?",
            "seven years",
        ),
        (
            "How long must customer records be kept?",
            "seven years",
        ),
        (
            "What security controls are required for protecting customer information?",
            "security controls",
        ),
        (
            "What encryption requirements apply?",
            "aes-256",
        ),
    ],
)
def test_real_embeddings_semantic_queries(
    db_session: Session,
    real_embedded_document: dict[str, Any],
    query: str,
    expected_snippet: str,
) -> None:
    retriever = Retriever(db_session)
    response = retriever.retrieve(
        query,
        top_k=5,
        filters=RetrievalFilters(document_id=real_embedded_document["version_id"]),
    )

    assert response.total_results >= 1
    assert any(expected_snippet in result.text.lower() for result in response.results[:3])


@pytest.mark.integration
@pytest.mark.slow
def test_real_embeddings_unrelated_query_is_low_confidence(
    db_session: Session,
    real_embedded_document: dict[str, Any],
) -> None:
    retriever = Retriever(db_session)
    response = retriever.retrieve(
        "What is the capital of France?",
        top_k=5,
        filters=RetrievalFilters(document_id=real_embedded_document["version_id"]),
    )

    assert response.total_results >= 1
    assert response.results[0].similarity < 0.55
