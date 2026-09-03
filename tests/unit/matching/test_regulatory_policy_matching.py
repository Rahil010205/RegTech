"""Unit tests for regulatory-to-policy matching control flow."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import EmbeddingModelError, NotFoundError, ValidationError
from app.models.clause import EMBEDDING_DIMENSION, Clause
from app.models.organization import Organization
from app.retrieval.organization_vector_search import OrganizationPolicySearchRow
from app.services.regulatory_policy_matching import RegulatoryPolicyMatchingService


def _clause(*, embedding: list[float] | None) -> Clause:
    clause = Clause(
        version_id=uuid4(),
        clause_number="10.2",
        section="Customer Identification",
        title="Identity verification",
        text="The regulated entity shall identify and verify the identity of customers before establishing a business relationship.",
        embedding=embedding,
    )
    clause.id = uuid4()
    clause.version = None
    return clause


def _row(similarity: float, content: str) -> OrganizationPolicySearchRow:
    return OrganizationPolicySearchRow(
        chunk_id=uuid4(),
        document_id=uuid4(),
        document_name="company_kyc_policy.pdf",
        content=content,
        section_title="Customer Identification",
        clause_reference="1.1",
        similarity=similarity,
        metadata={},
        document_type="KYC_POLICY",
        document_version="2026.1",
    )


def _service(session: MagicMock, vector_search: MagicMock, embedding_service: MagicMock | None = None):
    return RegulatoryPolicyMatchingService(
        session,
        vector_search=vector_search,
        embedding_service=embedding_service or MagicMock(),
    )


def test_uses_stored_embedding_and_organization_filter() -> None:
    org_id = uuid4()
    embedding = [0.01] * EMBEDDING_DIMENSION
    clause = _clause(embedding=embedding)
    session = MagicMock()
    session.get.return_value = Organization(name="Acme", slug="acme")
    vector_search = MagicMock()
    vector_search.search.return_value = [
        _row(0.91, "The company shall identify and verify every customer before establishing a business relationship."),
        _row(0.82, "Customer identification information shall be reviewed for completeness before account activation."),
    ]
    embedding_service = MagicMock()
    service = _service(session, vector_search, embedding_service)
    service._load_clause = MagicMock(return_value=clause)

    response = service.match_regulatory_clause_to_policy(org_id, clause.id, top_k=5, similarity_threshold=0.60)

    embedding_service.embed_text.assert_not_called()
    vector_search.search.assert_called_once()
    args, kwargs = vector_search.search.call_args
    assert args[0] == embedding
    assert kwargs["organization_id"] == org_id
    assert kwargs["top_k"] == 5
    assert kwargs["min_similarity"] == 0.60
    assert response.total_results == 2
    assert response.results[0].rank == 1
    assert response.results[0].similarity == 0.91
    assert response.results[1].rank == 2
    assert "embedding" not in response.model_dump()
    assert response.regulatory_clause.reference == "10.2"


def test_generates_document_embedding_when_missing() -> None:
    org_id = uuid4()
    clause = _clause(embedding=None)
    generated = [0.02] * EMBEDDING_DIMENSION
    session = MagicMock()
    session.get.return_value = Organization(name="Acme", slug="acme")
    vector_search = MagicMock()
    vector_search.search.return_value = []
    embedding_service = MagicMock()
    embedding_service.embed_text.return_value = generated
    service = _service(session, vector_search, embedding_service)
    service._load_clause = MagicMock(return_value=clause)

    response = service.match_regulatory_clause_to_policy(org_id, clause.id)

    embedding_service.embed_text.assert_called_once_with(clause.text)
    embedding_service.embed_query.assert_not_called()
    assert clause.embedding == generated
    session.commit.assert_called()
    assert args_query_embedding(vector_search) == generated
    assert response.total_results == 0
    assert response.results == []


def args_query_embedding(vector_search: MagicMock) -> list[float]:
    return vector_search.search.call_args[0][0]


def test_dimension_mismatch_raises_controlled_error() -> None:
    org_id = uuid4()
    clause = _clause(embedding=[0.1] * 8)
    session = MagicMock()
    session.get.return_value = Organization(name="Acme", slug="acme")
    service = _service(session, MagicMock())
    service._load_clause = MagicMock(return_value=clause)

    with pytest.raises(EmbeddingModelError, match="dimension"):
        service.match_regulatory_clause_to_policy(org_id, clause.id)


def test_organization_not_found() -> None:
    session = MagicMock()
    session.get.return_value = None
    service = _service(session, MagicMock())
    with pytest.raises(NotFoundError):
        service.match_regulatory_clause_to_policy(uuid4(), uuid4())


def test_clause_not_found() -> None:
    session = MagicMock()
    session.get.return_value = Organization(name="Acme", slug="acme")
    session.scalars.return_value.unique.return_value.one_or_none.return_value = None
    service = _service(session, MagicMock())
    with pytest.raises(NotFoundError):
        service.match_regulatory_clause_to_policy(uuid4(), uuid4())


def test_invalid_top_k_and_threshold() -> None:
    session = MagicMock()
    session.get.return_value = Organization(name="Acme", slug="acme")
    service = _service(session, MagicMock())
    with pytest.raises(ValidationError):
        service.match_regulatory_clause_to_policy(uuid4(), uuid4(), top_k=0)
    with pytest.raises(ValidationError):
        service.match_regulatory_clause_to_policy(uuid4(), uuid4(), similarity_threshold=1.1)
