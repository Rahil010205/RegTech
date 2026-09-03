"""API tests for regulatory-policy matching endpoint."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.api.dependencies.services import get_regulatory_policy_matching_service
from app.api.schemas.matching import (
    MatchedRegulatoryClause,
    RegulatoryPolicyMatchHit,
    RegulatoryPolicyMatchResponse,
)
from app.core.exceptions import NotFoundError


def test_match_endpoint_returns_ranked_evidence(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()
    mock_service = MagicMock()
    mock_service.match_regulatory_clause_to_policy.return_value = RegulatoryPolicyMatchResponse(
        organization_id=org_id,
        regulatory_clause_id=clause_id,
        top_k=5,
        similarity_threshold=0.60,
        total_results=2,
        regulatory_clause=MatchedRegulatoryClause(
            id=clause_id,
            reference="10.2",
            content="The regulated entity shall identify and verify customers.",
        ),
        results=[
            RegulatoryPolicyMatchHit(
                chunk_id=uuid4(),
                document_id=uuid4(),
                document_name="company_kyc_policy.pdf",
                document_type="KYC_POLICY",
                document_version="2026.1",
                content="The company shall identify and verify every customer before establishing a business relationship.",
                section_title="Customer Identification",
                clause_reference="1.1",
                similarity=0.91,
                rank=1,
            ),
            RegulatoryPolicyMatchHit(
                chunk_id=uuid4(),
                document_id=uuid4(),
                content="Customer identification information shall be reviewed for completeness.",
                section_title="Customer Due Diligence",
                clause_reference="2.3",
                similarity=0.82,
                rank=2,
            ),
        ],
    )
    client.app.dependency_overrides[get_regulatory_policy_matching_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/compliance/match",
            json={"regulatory_clause_id": str(clause_id), "top_k": 5, "similarity_threshold": 0.60},
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_results"] == 2
    assert payload["results"][0]["rank"] == 1
    assert payload["results"][0]["similarity"] == 0.91
    assert "embedding" not in payload
    assert "embedding" not in payload["results"][0]
    mock_service.match_regulatory_clause_to_policy.assert_called_once()


def test_match_endpoint_empty_results(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()
    mock_service = MagicMock()
    mock_service.match_regulatory_clause_to_policy.return_value = RegulatoryPolicyMatchResponse(
        organization_id=org_id,
        regulatory_clause_id=clause_id,
        top_k=5,
        similarity_threshold=0.60,
        total_results=0,
        regulatory_clause=MatchedRegulatoryClause(id=clause_id, reference="99", content="cybersecurity"),
        results=[],
    )
    client.app.dependency_overrides[get_regulatory_policy_matching_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/compliance/match",
            json={"regulatory_clause_id": str(clause_id)},
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total_results"] == 0
    assert response.json()["results"] == []


def test_match_endpoint_rejects_invalid_top_k(client) -> None:
    org_id = uuid4()
    clause_id = str(uuid4())
    zero = client.post(
        f"/api/v1/organizations/{org_id}/compliance/match",
        json={"regulatory_clause_id": clause_id, "top_k": 0},
    )
    too_high = client.post(
        f"/api/v1/organizations/{org_id}/compliance/match",
        json={"regulatory_clause_id": clause_id, "top_k": 51},
    )
    assert zero.status_code == 422
    assert too_high.status_code == 422


def test_match_endpoint_rejects_invalid_threshold(client) -> None:
    org_id = uuid4()
    clause_id = str(uuid4())
    high = client.post(
        f"/api/v1/organizations/{org_id}/compliance/match",
        json={"regulatory_clause_id": clause_id, "similarity_threshold": 1.1},
    )
    low = client.post(
        f"/api/v1/organizations/{org_id}/compliance/match",
        json={"regulatory_clause_id": clause_id, "similarity_threshold": -0.1},
    )
    assert high.status_code == 422
    assert low.status_code == 422


def test_match_endpoint_rejects_invalid_uuid(client) -> None:
    response = client.post(
        f"/api/v1/organizations/{uuid4()}/compliance/match",
        json={"regulatory_clause_id": "not-a-uuid"},
    )
    assert response.status_code == 422


def test_match_endpoint_organization_not_found(client) -> None:
    org_id = uuid4()
    mock_service = MagicMock()
    mock_service.match_regulatory_clause_to_policy.side_effect = NotFoundError(
        "Organization", str(org_id)
    )
    client.app.dependency_overrides[get_regulatory_policy_matching_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/compliance/match",
            json={"regulatory_clause_id": str(uuid4())},
        )
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 404


def test_match_endpoint_clause_not_found(client) -> None:
    clause_id = uuid4()
    mock_service = MagicMock()
    mock_service.match_regulatory_clause_to_policy.side_effect = NotFoundError(
        "Regulatory clause", str(clause_id)
    )
    client.app.dependency_overrides[get_regulatory_policy_matching_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{uuid4()}/compliance/match",
            json={"regulatory_clause_id": str(clause_id)},
        )
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 404
