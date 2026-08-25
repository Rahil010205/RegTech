"""API tests for semantic search endpoint."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.api.dependencies.services import get_search_service
from app.retrieval.schemas import RetrievedClause, RetrievalResponse


def test_search_endpoint_returns_results(client):
    clause_id = uuid4()
    document_id = uuid4()
    mock_service = MagicMock()
    mock_service.search_clauses.return_value = RetrievalResponse(
        query="What are the requirements for customer data retention?",
        top_k=5,
        min_similarity=None,
        total_results=1,
        results=[
            RetrievedClause(
                clause_id=clause_id,
                document_id=document_id,
                document_name="RBI Data Retention",
                regulator="RBI",
                clause_number="4.1",
                section="Data Retention",
                text="The organization shall retain customer records for seven years.",
                page_number=18,
                similarity=0.91,
                metadata={"regulator": "RBI"},
            )
        ],
    )

    client.app.dependency_overrides[get_search_service] = lambda: mock_service
    try:
        response = client.post(
            "/api/v1/search",
            json={
                "query": "What are the requirements for customer data retention?",
                "top_k": 5,
            },
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_results"] == 1
    assert payload["results"][0]["clause_number"] == "4.1"
    assert payload["results"][0]["similarity"] == 0.91


def test_search_endpoint_rejects_empty_query(client):
    response = client.post("/api/v1/search", json={"query": "   "})
    assert response.status_code == 422


def test_search_endpoint_rejects_invalid_top_k(client):
    response = client.post(
        "/api/v1/search",
        json={"query": "data retention", "top_k": 0},
    )
    assert response.status_code == 422


def test_search_endpoint_rejects_invalid_threshold(client):
    response = client.post(
        "/api/v1/search",
        json={"query": "data retention", "min_similarity": 1.5},
    )
    assert response.status_code == 422
