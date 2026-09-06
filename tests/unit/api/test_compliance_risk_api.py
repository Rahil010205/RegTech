"""API unit tests for Step 3 compliance risk assessment endpoint."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.api.dependencies.services import get_compliance_risk_scoring_service
from app.api.schemas.risk_scoring import (
    GapSeverity,
    IdentifiedGap,
    RiskFactorBreakdown,
    RiskFactorDetail,
    RiskLevel,
    RiskScoringResponse,
)
from app.core.exceptions import NotFoundError


def _mock_risk_response(
    org_id, clause_id, score=86.25, level=RiskLevel.CRITICAL
) -> RiskScoringResponse:
    return RiskScoringResponse(
        id=uuid4(),
        organization_id=org_id,
        regulatory_clause_id=clause_id,
        compliance_status="NON_COMPLIANT",
        risk_score=score,
        risk_level=level,
        confidence=0.85,
        factor_breakdown=RiskFactorBreakdown(
            compliance_severity=RiskFactorDetail(
                value=1.0, weight=0.40, contribution=40.0, description="Status NON_COMPLIANT"
            ),
            regulatory_criticality=RiskFactorDetail(
                value=0.75, weight=0.20, contribution=15.0, description="Criticality HIGH"
            ),
            gap_severity=RiskFactorDetail(
                value=0.75, weight=0.15, contribution=11.25, description="High gap"
            ),
            evidence_strength=RiskFactorDetail(
                value=0.80, weight=0.15, contribution=12.0, description="Evidence similarity 0.80"
            ),
            confidence=RiskFactorDetail(
                value=0.85, weight=0.10, contribution=8.50, description="Confidence 0.85"
            ),
        ),
        identified_gaps=[
            IdentifiedGap(
                description="Policy lacks mandatory customer verification controls.",
                severity=GapSeverity.HIGH,
            )
        ],
        explanation="Assessed compliance risk score is 86.25 (CRITICAL).",
    )


def test_risk_endpoint_valid_request(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()

    mock_service = MagicMock()
    mock_service.evaluate_risk.return_value = _mock_risk_response(org_id, clause_id)

    client.app.dependency_overrides[get_compliance_risk_scoring_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/compliance/risk",
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
    assert payload["compliance_status"] == "NON_COMPLIANT"
    assert payload["risk_score"] == 86.25
    assert payload["risk_level"] == "CRITICAL"
    assert payload["confidence"] == 0.85
    assert "factor_breakdown" in payload
    assert len(payload["identified_gaps"]) == 1
    assert payload["identified_gaps"][0]["severity"] == "HIGH"
    assert "Assessed compliance risk score is 86.25 (CRITICAL)" in payload["explanation"]


def test_risk_endpoint_invalid_top_k_zero(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()
    response = client.post(
        f"/api/v1/organizations/{org_id}/compliance/risk",
        json={
            "regulatory_clause_id": str(clause_id),
            "top_k": 0,
            "similarity_threshold": 0.60,
        },
    )
    assert response.status_code == 422


def test_risk_endpoint_invalid_top_k_exceeds_max(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()
    response = client.post(
        f"/api/v1/organizations/{org_id}/compliance/risk",
        json={
            "regulatory_clause_id": str(clause_id),
            "top_k": 51,
            "similarity_threshold": 0.60,
        },
    )
    assert response.status_code == 422


def test_risk_endpoint_invalid_threshold_negative(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()
    response = client.post(
        f"/api/v1/organizations/{org_id}/compliance/risk",
        json={
            "regulatory_clause_id": str(clause_id),
            "top_k": 5,
            "similarity_threshold": -0.1,
        },
    )
    assert response.status_code == 422


def test_risk_endpoint_invalid_threshold_above_one(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()
    response = client.post(
        f"/api/v1/organizations/{org_id}/compliance/risk",
        json={
            "regulatory_clause_id": str(clause_id),
            "top_k": 5,
            "similarity_threshold": 1.1,
        },
    )
    assert response.status_code == 422


def test_risk_endpoint_invalid_uuid(client) -> None:
    response = client.post(
        "/api/v1/organizations/not-a-valid-uuid/compliance/risk",
        json={"regulatory_clause_id": str(uuid4())},
    )
    assert response.status_code == 422


def test_risk_endpoint_unknown_organization(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()

    mock_service = MagicMock()
    mock_service.evaluate_risk.side_effect = NotFoundError("Organization", str(org_id))

    client.app.dependency_overrides[get_compliance_risk_scoring_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/compliance/risk",
            json={"regulatory_clause_id": str(clause_id)},
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 404
    payload = response.json()
    assert payload["error_code"] == "NOT_FOUND"
    assert str(org_id) in payload["message"]


def test_risk_endpoint_unknown_regulatory_clause(client) -> None:
    org_id = uuid4()
    clause_id = uuid4()

    mock_service = MagicMock()
    mock_service.evaluate_risk.side_effect = NotFoundError("Regulatory clause", str(clause_id))

    client.app.dependency_overrides[get_compliance_risk_scoring_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/compliance/risk",
            json={"regulatory_clause_id": str(clause_id)},
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 404
    payload = response.json()
    assert payload["error_code"] == "NOT_FOUND"
    assert str(clause_id) in payload["message"]


def test_risk_endpoint_zero_sensitive_data_exposure(client) -> None:
    """Ensure API response contains zero sensitive fields (no API keys, prompts, embeddings)."""
    org_id = uuid4()
    clause_id = uuid4()

    mock_service = MagicMock()
    mock_service.evaluate_risk.return_value = _mock_risk_response(org_id, clause_id)

    client.app.dependency_overrides[get_compliance_risk_scoring_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/compliance/risk",
            json={"regulatory_clause_id": str(clause_id)},
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    raw_text = response.text
    assert "api_key" not in raw_text.lower()
    assert "authorization" not in raw_text.lower()
    assert "embedding" not in raw_text.lower()
    assert "system_prompt" not in raw_text.lower()


def test_risk_endpoint_organization_isolation(client) -> None:
    """Ensure requests are isolated by organization_id path parameter."""
    org_a = uuid4()
    org_b = uuid4()
    clause_id = uuid4()

    mock_service = MagicMock()
    mock_service.evaluate_risk.side_effect = [
        _mock_risk_response(org_a, clause_id),
        _mock_risk_response(org_b, clause_id),
    ]

    client.app.dependency_overrides[get_compliance_risk_scoring_service] = lambda: mock_service
    try:
        response_a = client.post(
            f"/api/v1/organizations/{org_a}/compliance/risk",
            json={"regulatory_clause_id": str(clause_id)},
        )
        assert response_a.status_code == 200

        response_b = client.post(
            f"/api/v1/organizations/{org_b}/compliance/risk",
            json={"regulatory_clause_id": str(clause_id)},
        )
        assert response_b.status_code == 200

        assert mock_service.evaluate_risk.call_count == 2
        mock_service.evaluate_risk.assert_any_call(
            organization_id=org_a,
            regulatory_clause_id=clause_id,
            top_k=5,
            similarity_threshold=0.60,
        )
        mock_service.evaluate_risk.assert_any_call(
            organization_id=org_b,
            regulatory_clause_id=clause_id,
            top_k=5,
            similarity_threshold=0.60,
        )
    finally:
        client.app.dependency_overrides.clear()
