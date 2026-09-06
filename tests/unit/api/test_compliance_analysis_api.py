"""API unit tests for LLM-based compliance analysis endpoint."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.api.dependencies.services import get_compliance_analysis_service
from app.api.schemas.compliance_analysis import (
    ComplianceAnalysisResponse,
    EvidenceReference,
)
from app.core.exceptions import NotFoundError


def test_analyze_endpoint_valid_request(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()
    chunk_id = uuid4()
    doc_id = uuid4()

    mock_service = MagicMock()
    mock_service.analyze.return_value = ComplianceAnalysisResponse(
        organization_id=org_id,
        regulatory_clause_id=clause_id,
        compliance_status="COMPLIANT",
        confidence=0.93,
        reasoning="The organization policy directly addresses the regulatory requirement.",
        evidence=[
            EvidenceReference(
                chunk_id=chunk_id,
                document_id=doc_id,
                similarity=0.91,
                relevance="supports",
                explanation="The policy explicitly requires customer identification and verification.",
            )
        ],
        gaps=[],
    )

    client.app.dependency_overrides[get_compliance_analysis_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/compliance/analyze",
            json={
                "regulatory_clause_id": str(clause_id),
                "top_k": 5,
                "similarity_threshold": 0.60,
            },
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["organization_id"] == str(org_id)
    assert payload["regulatory_clause_id"] == str(clause_id)
    assert payload["compliance_status"] == "COMPLIANT"
    assert payload["confidence"] == 0.93
    assert len(payload["evidence"]) == 1
    assert payload["evidence"][0]["chunk_id"] == str(chunk_id)
    assert payload["gaps"] == []


def test_analyze_endpoint_invalid_top_k_zero(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()
    response = client.post(
        f"/api/v1/organizations/{org_id}/compliance/analyze",
        json={
            "regulatory_clause_id": str(clause_id),
            "top_k": 0,
            "similarity_threshold": 0.60,
        },
    )
    assert response.status_code == 422


def test_analyze_endpoint_invalid_top_k_exceeds_max(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()
    response = client.post(
        f"/api/v1/organizations/{org_id}/compliance/analyze",
        json={
            "regulatory_clause_id": str(clause_id),
            "top_k": 51,
            "similarity_threshold": 0.60,
        },
    )
    assert response.status_code == 422


def test_analyze_endpoint_invalid_threshold_negative(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()
    response = client.post(
        f"/api/v1/organizations/{org_id}/compliance/analyze",
        json={
            "regulatory_clause_id": str(clause_id),
            "top_k": 5,
            "similarity_threshold": -0.1,
        },
    )
    assert response.status_code == 422


def test_analyze_endpoint_invalid_threshold_above_one(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()
    response = client.post(
        f"/api/v1/organizations/{org_id}/compliance/analyze",
        json={
            "regulatory_clause_id": str(clause_id),
            "top_k": 5,
            "similarity_threshold": 1.1,
        },
    )
    assert response.status_code == 422


def test_analyze_endpoint_invalid_uuid(client) -> None:
    org_id = uuid4()
    response = client.post(
        f"/api/v1/organizations/{org_id}/compliance/analyze",
        json={
            "regulatory_clause_id": "not-a-valid-uuid",
            "top_k": 5,
            "similarity_threshold": 0.60,
        },
    )
    assert response.status_code == 422


def test_analyze_endpoint_unknown_organization(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()

    mock_service = MagicMock()
    mock_service.analyze.side_effect = NotFoundError("Organization", str(org_id))

    client.app.dependency_overrides[get_compliance_analysis_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/compliance/analyze",
            json={
                "regulatory_clause_id": str(clause_id),
                "top_k": 5,
                "similarity_threshold": 0.60,
            },
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 404
    payload = response.json()
    assert payload["error_code"] == "NOT_FOUND"
    assert str(org_id) in payload["message"]


def test_analyze_endpoint_unknown_regulatory_clause(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()

    mock_service = MagicMock()
    mock_service.analyze.side_effect = NotFoundError("Regulatory clause", str(clause_id))

    client.app.dependency_overrides[get_compliance_analysis_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/compliance/analyze",
            json={
                "regulatory_clause_id": str(clause_id),
                "top_k": 5,
                "similarity_threshold": 0.60,
            },
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 404
    payload = response.json()
    assert payload["error_code"] == "NOT_FOUND"
    assert str(clause_id) in payload["message"]


def test_analyze_endpoint_no_evidence(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()

    mock_service = MagicMock()
    mock_service.analyze.return_value = ComplianceAnalysisResponse(
        organization_id=org_id,
        regulatory_clause_id=clause_id,
        compliance_status="INSUFFICIENT_EVIDENCE",
        confidence=0.0,
        reasoning="No sufficiently relevant organization policy evidence was found.",
        evidence=[],
        gaps=["No relevant organization policy evidence was retrieved."],
    )

    client.app.dependency_overrides[get_compliance_analysis_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/compliance/analyze",
            json={
                "regulatory_clause_id": str(clause_id),
                "top_k": 5,
                "similarity_threshold": 0.60,
            },
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["compliance_status"] == "INSUFFICIENT_EVIDENCE"
    assert payload["confidence"] == 0.0
    assert payload["evidence"] == []
    assert payload["gaps"] == ["No relevant organization policy evidence was retrieved."]
