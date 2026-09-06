"""Unit tests for Step 3 Compliance Risk Scoring & Severity Engine."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from app.api.schemas.compliance_analysis import (
    ComplianceAnalysisResponse,
    EvidenceReference,
)
from app.api.schemas.risk_scoring import GapSeverity, IdentifiedGap, RiskLevel
from app.core.config import Settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.clause import Clause
from app.models.compliance_risk_assessment import ComplianceRiskAssessment
from app.models.organization import Organization
from app.services.compliance_risk_scoring import (
    ComplianceRiskScoringService,
    determine_risk_level,
)


@pytest.fixture
def risk_service() -> ComplianceRiskScoringService:
    mock_compliance_service = MagicMock()
    return ComplianceRiskScoringService(
        compliance_analysis_service=mock_compliance_service,
        settings=Settings(),
    )


def test_weights_sum_to_one() -> None:
    """Validate that configured risk scoring weights sum exactly to 1.0 (100%)."""
    settings = Settings()
    total_weight = (
        settings.risk_weight_compliance_severity
        + settings.risk_weight_regulatory_criticality
        + settings.risk_weight_gap_severity
        + settings.risk_weight_evidence_strength
        + settings.risk_weight_confidence
    )
    assert abs(total_weight - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# 1. Basic Scoring Tests
# ---------------------------------------------------------------------------


def test_compliant_produces_low_risk(risk_service: ComplianceRiskScoringService) -> None:
    """COMPLIANT status with low criticality, no gaps, and reasonable evidence produces LOW risk."""
    score, level, breakdown, gaps, explanation = risk_service.calculate_risk(
        compliance_status="COMPLIANT",
        confidence=0.50,
        evidence=[
            EvidenceReference(
                chunk_id=uuid4(),
                document_id=uuid4(),
                similarity=0.60,
                relevance="supports",
                explanation="Valid evidence",
            )
        ],
        gaps=[],
        regulatory_criticality="LOW",
    )

    # compliance: 0.0 * 40 = 0.0
    # criticality: 0.25 * 20 = 5.0
    # gaps: 0.0 * 15 = 0.0
    # evidence: 0.60 * 15 = 9.0
    # confidence: 0.50 * 10 = 5.0
    # total = 19.0 -> LOW (<20)
    assert score == 19.0
    assert level == RiskLevel.LOW
    assert breakdown.compliance_severity.contribution == 0.0
    assert breakdown.gap_severity.contribution == 0.0
    assert "Assessed compliance risk score is 19.00 (LOW)" in explanation


def test_partially_compliant_produces_higher_risk(
    risk_service: ComplianceRiskScoringService,
) -> None:
    """PARTIALLY_COMPLIANT status produces higher risk than COMPLIANT."""
    comp_score, _, _, _, _ = risk_service.calculate_risk(
        compliance_status="COMPLIANT",
        confidence=0.80,
        evidence=[],
        gaps=[],
        regulatory_criticality="MEDIUM",
    )
    partial_score, partial_level, breakdown, _, _ = risk_service.calculate_risk(
        compliance_status="PARTIALLY_COMPLIANT",
        confidence=0.80,
        evidence=[],
        gaps=["Minor procedure gap"],
        regulatory_criticality="MEDIUM",
    )

    assert partial_score > comp_score
    assert partial_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert breakdown.compliance_severity.value == 0.50
    assert breakdown.compliance_severity.contribution == 20.0


def test_non_compliant_produces_high_or_critical_risk(
    risk_service: ComplianceRiskScoringService,
) -> None:
    """NON_COMPLIANT status produces HIGH or CRITICAL risk."""
    score, level, breakdown, _, _ = risk_service.calculate_risk(
        compliance_status="NON_COMPLIANT",
        confidence=0.90,
        evidence=[
            EvidenceReference(
                chunk_id=uuid4(),
                document_id=uuid4(),
                similarity=0.85,
                relevance="contradicts",
                explanation="Contradicts requirement",
            )
        ],
        gaps=["Completely absent control for customer data encryption"],
        regulatory_criticality="HIGH",
    )

    # compliance: 1.0 * 40 = 40.0
    # criticality: 0.75 * 20 = 15.0
    # gaps (absent -> HIGH 0.75): 0.75 * 15 = 11.25
    # evidence: 0.85 * 15 = 12.75
    # confidence: 0.90 * 10 = 9.0
    # total = 88.0 -> CRITICAL (>= 70)
    assert score >= 70.0
    assert level == RiskLevel.CRITICAL
    assert breakdown.compliance_severity.value == 1.00
    assert breakdown.compliance_severity.contribution == 40.0


def test_insufficient_evidence_produces_uncertainty_risk(
    risk_service: ComplianceRiskScoringService,
) -> None:
    """INSUFFICIENT_EVIDENCE carries baseline uncertainty risk (0.60 severity)."""
    score, level, breakdown, _, explanation = risk_service.calculate_risk(
        compliance_status="INSUFFICIENT_EVIDENCE",
        confidence=0.0,
        evidence=[],
        gaps=["No relevant evidence found"],
        regulatory_criticality="MEDIUM",
    )

    # compliance: 0.60 * 40 = 24.0
    # criticality: 0.50 * 20 = 10.0
    # gaps: 0.50 * 15 = 7.50
    # evidence: 0.0 * 15 = 0.0
    # confidence: 0.0 * 10 = 0.0
    # total = 41.50 -> HIGH (40-69.99)
    assert score == 41.50
    assert level == RiskLevel.HIGH
    assert breakdown.compliance_severity.value == 0.60
    assert breakdown.compliance_severity.contribution == 24.0
    assert "uncertainty" in explanation.lower()
    assert "absence of evidence cannot be treated as compliant" in explanation.lower()


# ---------------------------------------------------------------------------
# 2. Boundary Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("score", "expected_level"),
    [
        (0.00, RiskLevel.LOW),
        (10.50, RiskLevel.LOW),
        (19.99, RiskLevel.LOW),
        (20.00, RiskLevel.MEDIUM),
        (25.00, RiskLevel.MEDIUM),
        (39.99, RiskLevel.MEDIUM),
        (40.00, RiskLevel.HIGH),
        (55.00, RiskLevel.HIGH),
        (69.99, RiskLevel.HIGH),
        (70.00, RiskLevel.CRITICAL),
        (85.50, RiskLevel.CRITICAL),
        (100.00, RiskLevel.CRITICAL),
    ],
)
def test_risk_level_boundaries(score: float, expected_level: RiskLevel) -> None:
    """Verify exact boundary mapping between numeric scores and RiskLevels."""
    assert determine_risk_level(score) == expected_level


# ---------------------------------------------------------------------------
# 3. Factor Validation Tests
# ---------------------------------------------------------------------------


def test_negative_confidence_raises_validation_error(
    risk_service: ComplianceRiskScoringService,
) -> None:
    with pytest.raises(ValidationError, match="Confidence must be between 0.0 and 1.0"):
        risk_service.calculate_risk(
            compliance_status="COMPLIANT",
            confidence=-0.01,
            evidence=[],
            gaps=[],
        )


def test_confidence_above_one_raises_validation_error(
    risk_service: ComplianceRiskScoringService,
) -> None:
    with pytest.raises(ValidationError, match="Confidence must be between 0.0 and 1.0"):
        risk_service.calculate_risk(
            compliance_status="COMPLIANT",
            confidence=1.01,
            evidence=[],
            gaps=[],
        )


def test_invalid_compliance_status_raises_validation_error(
    risk_service: ComplianceRiskScoringService,
) -> None:
    with pytest.raises(ValidationError, match="Invalid compliance status"):
        risk_service.calculate_risk(
            compliance_status="UNKNOWN_STATUS",
            confidence=0.8,
            evidence=[],
            gaps=[],
        )


def test_invalid_regulatory_criticality_raises_validation_error(
    risk_service: ComplianceRiskScoringService,
) -> None:
    with pytest.raises(ValidationError, match="Invalid regulatory criticality"):
        risk_service.calculate_risk(
            compliance_status="COMPLIANT",
            confidence=0.8,
            evidence=[],
            gaps=[],
            regulatory_criticality="SUPER_HIGH",
        )


# ---------------------------------------------------------------------------
# 4. Evidence Strength Tests
# ---------------------------------------------------------------------------


def test_evidence_strength_no_evidence_is_zero(
    risk_service: ComplianceRiskScoringService,
) -> None:
    _, _, breakdown, _, _ = risk_service.calculate_risk(
        compliance_status="COMPLIANT",
        confidence=0.5,
        evidence=[],
        gaps=[],
    )
    assert breakdown.evidence_strength.value == 0.0
    assert breakdown.evidence_strength.contribution == 0.0


def test_evidence_strength_averages_verified_similarity(
    risk_service: ComplianceRiskScoringService,
) -> None:
    evidence = [
        EvidenceReference(
            chunk_id=uuid4(),
            document_id=uuid4(),
            similarity=0.70,
            relevance="supports",
            explanation="Evidence 1",
        ),
        EvidenceReference(
            chunk_id=uuid4(),
            document_id=uuid4(),
            similarity=0.90,
            relevance="supports",
            explanation="Evidence 2",
        ),
    ]
    _, _, breakdown, _, _ = risk_service.calculate_risk(
        compliance_status="COMPLIANT",
        confidence=0.5,
        evidence=evidence,
        gaps=[],
    )
    # Average of 0.70 and 0.90 is 0.80
    assert breakdown.evidence_strength.value == 0.80
    assert breakdown.evidence_strength.contribution == round(0.80 * 15.0, 2)


# ---------------------------------------------------------------------------
# 5. Gap Severity Tests
# ---------------------------------------------------------------------------


def test_no_gaps_gives_zero_gap_severity(
    risk_service: ComplianceRiskScoringService,
) -> None:
    _, _, breakdown, identified_gaps, _ = risk_service.calculate_risk(
        compliance_status="COMPLIANT",
        confidence=0.5,
        evidence=[],
        gaps=[],
    )
    assert breakdown.gap_severity.value == 0.0
    assert breakdown.gap_severity.contribution == 0.0
    assert identified_gaps == []


def test_single_low_gap(risk_service: ComplianceRiskScoringService) -> None:
    _, _, breakdown, identified_gaps, _ = risk_service.calculate_risk(
        compliance_status="COMPLIANT",
        confidence=0.5,
        evidence=[],
        gaps=["Minor formatting and documentation guideline update recommended."],
    )
    assert len(identified_gaps) == 1
    assert identified_gaps[0].severity == GapSeverity.LOW
    assert breakdown.gap_severity.value == 0.25
    assert breakdown.gap_severity.contribution == round(0.25 * 15.0, 2)


def test_single_medium_gap(risk_service: ComplianceRiskScoringService) -> None:
    _, _, breakdown, identified_gaps, _ = risk_service.calculate_risk(
        compliance_status="PARTIALLY_COMPLIANT",
        confidence=0.5,
        evidence=[],
        gaps=["Policy does not specify verification procedure for all customer categories."],
    )
    assert len(identified_gaps) == 1
    assert identified_gaps[0].severity == GapSeverity.MEDIUM
    assert breakdown.gap_severity.value == 0.50
    assert breakdown.gap_severity.contribution == round(0.50 * 15.0, 2)


def test_single_high_gap(risk_service: ComplianceRiskScoringService) -> None:
    _, _, breakdown, identified_gaps, _ = risk_service.calculate_risk(
        compliance_status="PARTIALLY_COMPLIANT",
        confidence=0.5,
        evidence=[],
        gaps=["Policy completely lacks mandatory controls for customer identification."],
    )
    assert len(identified_gaps) == 1
    assert identified_gaps[0].severity == GapSeverity.HIGH
    assert breakdown.gap_severity.value == 0.75
    assert breakdown.gap_severity.contribution == round(0.75 * 15.0, 2)


def test_single_critical_gap(risk_service: ComplianceRiskScoringService) -> None:
    _, _, breakdown, identified_gaps, _ = risk_service.calculate_risk(
        compliance_status="NON_COMPLIANT",
        confidence=0.5,
        evidence=[],
        gaps=["Severe unauthorized data access breach with zero protected controls."],
    )
    assert len(identified_gaps) == 1
    assert identified_gaps[0].severity == GapSeverity.CRITICAL
    assert breakdown.gap_severity.value == 1.00
    assert breakdown.gap_severity.contribution == round(1.00 * 15.0, 2)


def test_multiple_gaps_aggregates_max_severity(
    risk_service: ComplianceRiskScoringService,
) -> None:
    _, _, breakdown, identified_gaps, _ = risk_service.calculate_risk(
        compliance_status="PARTIALLY_COMPLIANT",
        confidence=0.5,
        evidence=[],
        gaps=[
            "Minor formatting issue.",  # LOW
            "Policy does not specify procedure.",  # MEDIUM
            "Critical unencrypted database breach risk.",  # CRITICAL
        ],
    )
    assert len(identified_gaps) == 3
    # Max severity among LOW, MEDIUM, CRITICAL is CRITICAL (1.00)
    assert breakdown.gap_severity.value == 1.00
    assert breakdown.gap_severity.contribution == 15.0


def test_structured_gaps_input_preserved(
    risk_service: ComplianceRiskScoringService,
) -> None:
    gaps_input = [
        {"description": "Explicit critical gap", "severity": "CRITICAL"},
        IdentifiedGap(description="Explicit low gap", severity=GapSeverity.LOW),
    ]
    _, _, breakdown, identified_gaps, _ = risk_service.calculate_risk(
        compliance_status="PARTIALLY_COMPLIANT",
        confidence=0.5,
        evidence=[],
        gaps=gaps_input,
    )
    assert len(identified_gaps) == 2
    assert identified_gaps[0].severity == GapSeverity.CRITICAL
    assert identified_gaps[1].severity == GapSeverity.LOW
    assert breakdown.gap_severity.value == 1.00


# ---------------------------------------------------------------------------
# 6. Regulatory Criticality Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("crit", "expected_val", "expected_contrib"),
    [
        ("LOW", 0.25, 5.00),
        ("MEDIUM", 0.50, 10.00),
        ("HIGH", 0.75, 15.00),
        ("CRITICAL", 1.00, 20.00),
    ],
)
def test_regulatory_criticality_mapping(
    risk_service: ComplianceRiskScoringService,
    crit: str,
    expected_val: float,
    expected_contrib: float,
) -> None:
    _, _, breakdown, _, _ = risk_service.calculate_risk(
        compliance_status="COMPLIANT",
        confidence=0.5,
        evidence=[],
        gaps=[],
        regulatory_criticality=crit,
    )
    assert breakdown.regulatory_criticality.value == expected_val
    assert breakdown.regulatory_criticality.contribution == expected_contrib


# ---------------------------------------------------------------------------
# 7. Determinism Test
# ---------------------------------------------------------------------------


def test_scoring_determinism(risk_service: ComplianceRiskScoringService) -> None:
    """Repeated runs with the exact same input must yield identical scores and factor breakdown."""
    args = {
        "compliance_status": "PARTIALLY_COMPLIANT",
        "confidence": 0.82,
        "evidence": [
            EvidenceReference(
                chunk_id=uuid4(),
                document_id=uuid4(),
                similarity=0.88,
                relevance="partially_supports",
                explanation="Evidence chunk",
            )
        ],
        "gaps": ["Policy lacks procedure for non-individual customers."],
        "regulatory_criticality": "HIGH",
    }

    result1 = risk_service.calculate_risk(**args)
    result2 = risk_service.calculate_risk(**args)

    assert result1[0] == result2[0]
    assert result1[1] == result2[1]
    assert result1[2].model_dump() == result2[2].model_dump()
    assert [g.model_dump() for g in result1[3]] == [g.model_dump() for g in result2[3]]
    assert result1[4] == result2[4]


# ---------------------------------------------------------------------------
# 8. Score from Analysis Bridge
# ---------------------------------------------------------------------------


def test_score_from_analysis_bridge(risk_service: ComplianceRiskScoringService) -> None:
    org_id = uuid4()
    clause_id = uuid4()
    analysis = ComplianceAnalysisResponse(
        organization_id=org_id,
        regulatory_clause_id=clause_id,
        compliance_status="NON_COMPLIANT",
        confidence=0.80,
        reasoning="Policy does not comply with customer verification requirements.",
        evidence=[
            EvidenceReference(
                chunk_id=uuid4(),
                document_id=uuid4(),
                similarity=0.80,
                relevance="contradicts",
                explanation="Contradicts mandatory controls",
            )
        ],
        gaps=["Completely absent verification controls."],
    )

    clause = Clause(
        clause_number="4.1",
        text="Customer identification clause",
        criticality="HIGH",
    )

    response = risk_service.score_from_analysis(analysis, clause=clause)

    assert response.organization_id == org_id
    assert response.regulatory_clause_id == clause_id
    assert response.compliance_status == "NON_COMPLIANT"
    assert response.factor_breakdown.compliance_severity.contribution == 40.0
    assert response.factor_breakdown.regulatory_criticality.contribution == 15.0  # HIGH = 0.75 * 20
    assert response.risk_score >= 70.0
    assert response.risk_level == RiskLevel.CRITICAL


# ---------------------------------------------------------------------------
# 9. evaluate_risk Pipeline & Database Persistence Tests
# ---------------------------------------------------------------------------


def test_evaluate_risk_full_pipeline_with_persistence() -> None:
    """Validate full evaluate_risk method including db lookups, Step 2B, and persistence."""
    org_id = uuid4()
    clause_id = uuid4()
    assessment_id = uuid4()

    mock_db = MagicMock()
    mock_org = Organization(id=org_id, name="Test Org", slug="test-org")
    mock_clause = Clause(
        id=clause_id,
        clause_number="5.1",
        text="Sample clause text",
        criticality="HIGH",
    )

    # Setup DB mock
    mock_db.get.return_value = mock_org
    mock_scalars = MagicMock()
    mock_scalars.unique.return_value.one_or_none.return_value = mock_clause
    mock_db.scalars.return_value = mock_scalars

    # Simulate refresh setting id
    def mock_refresh(instance):
        instance.id = assessment_id

    mock_db.refresh.side_effect = mock_refresh

    # Setup ComplianceAnalysisService mock
    mock_compliance_service = MagicMock()
    mock_compliance_service.analyze.return_value = ComplianceAnalysisResponse(
        organization_id=org_id,
        regulatory_clause_id=clause_id,
        compliance_status="COMPLIANT",
        confidence=0.90,
        reasoning="Compliant policy.",
        evidence=[
            EvidenceReference(
                chunk_id=uuid4(),
                document_id=uuid4(),
                similarity=0.85,
                relevance="supports",
                explanation="Evidence matches.",
            )
        ],
        gaps=[],
    )

    service = ComplianceRiskScoringService(
        compliance_analysis_service=mock_compliance_service,
        db_session=mock_db,
    )

    response = service.evaluate_risk(
        organization_id=org_id,
        regulatory_clause_id=clause_id,
        top_k=5,
        similarity_threshold=0.60,
    )

    # Verify lookups
    mock_db.get.assert_called_once_with(Organization, org_id)
    mock_compliance_service.analyze.assert_called_once_with(
        organization_id=org_id,
        regulatory_clause_id=clause_id,
        top_k=5,
        similarity_threshold=0.60,
    )

    # Verify persistence
    mock_db.add.assert_called_once()
    saved_record = mock_db.add.call_args[0][0]
    assert isinstance(saved_record, ComplianceRiskAssessment)
    assert saved_record.organization_id == org_id
    assert saved_record.regulatory_clause_id == clause_id
    assert saved_record.compliance_status == "COMPLIANT"
    assert saved_record.risk_score == response.risk_score
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(saved_record)

    # Verify response
    assert response.id == assessment_id
    assert response.compliance_status == "COMPLIANT"
    assert response.confidence == 0.90


def test_evaluate_risk_unknown_organization_raises_not_found() -> None:
    org_id = uuid4()
    clause_id = uuid4()

    mock_db = MagicMock()
    mock_db.get.return_value = None

    service = ComplianceRiskScoringService(
        compliance_analysis_service=MagicMock(),
        db_session=mock_db,
    )

    with pytest.raises(NotFoundError) as exc_info:
        service.evaluate_risk(organization_id=org_id, regulatory_clause_id=clause_id)

    assert "Organization" in str(exc_info.value)
    assert str(org_id) in str(exc_info.value)


def test_evaluate_risk_unknown_clause_raises_not_found() -> None:
    org_id = uuid4()
    clause_id = uuid4()

    mock_db = MagicMock()
    mock_db.get.return_value = Organization(id=org_id, name="Test Org", slug="test-org")
    mock_scalars = MagicMock()
    mock_scalars.unique.return_value.one_or_none.return_value = None
    mock_db.scalars.return_value = mock_scalars

    service = ComplianceRiskScoringService(
        compliance_analysis_service=MagicMock(),
        db_session=mock_db,
    )

    with pytest.raises(NotFoundError) as exc_info:
        service.evaluate_risk(organization_id=org_id, regulatory_clause_id=clause_id)

    assert "Regulatory clause" in str(exc_info.value)
    assert str(clause_id) in str(exc_info.value)


def test_evaluate_risk_without_db_session() -> None:
    org_id = uuid4()
    clause_id = uuid4()

    mock_compliance_service = MagicMock()
    mock_compliance_service.analyze.return_value = ComplianceAnalysisResponse(
        organization_id=org_id,
        regulatory_clause_id=clause_id,
        compliance_status="PARTIALLY_COMPLIANT",
        confidence=0.75,
        reasoning="Partial compliance.",
        evidence=[],
        gaps=["Missing secondary check."],
    )

    service = ComplianceRiskScoringService(
        compliance_analysis_service=mock_compliance_service,
        db_session=None,
    )

    response = service.evaluate_risk(organization_id=org_id, regulatory_clause_id=clause_id)

    assert response.id is None
    assert response.compliance_status == "PARTIALLY_COMPLIANT"
    assert response.confidence == 0.75
    assert response.factor_breakdown.regulatory_criticality.value == 0.50  # DEFAULT MEDIUM

