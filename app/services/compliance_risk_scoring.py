"""Compliance Risk Scoring & Severity Engine (Step 3).

Transforms verified Step 2B compliance analyses into deterministic, explainable
risk assessments based on transparent weighted factors without making any additional
LLM calls or vector searches.
"""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.compliance_analysis import (
    ComplianceAnalysisResponse,
    EvidenceReference,
)
from app.api.schemas.risk_scoring import (
    GapSeverity,
    IdentifiedGap,
    RiskFactorBreakdown,
    RiskFactorDetail,
    RiskLevel,
    RiskScoringResponse,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.clause import Clause
from app.models.compliance_risk_assessment import ComplianceRiskAssessment
from app.models.organization import Organization
from app.services.compliance_analysis import ComplianceAnalysisService

# Deterministic mappings
COMPLIANCE_SEVERITY_MAPPING: dict[str, float] = {
    "COMPLIANT": 0.00,
    "PARTIALLY_COMPLIANT": 0.50,
    "NON_COMPLIANT": 1.00,
    "INSUFFICIENT_EVIDENCE": 0.60,
}

REGULATORY_CRITICALITY_MAPPING: dict[str, float] = {
    "LOW": 0.25,
    "MEDIUM": 0.50,
    "HIGH": 0.75,
    "CRITICAL": 1.00,
}

GAP_SEVERITY_MAPPING: dict[str, float] = {
    "LOW": 0.25,
    "MEDIUM": 0.50,
    "HIGH": 0.75,
    "CRITICAL": 1.00,
}

# Boundary constants
RISK_LEVEL_LOW_UPPER = 20.00
RISK_LEVEL_MEDIUM_UPPER = 40.00
RISK_LEVEL_HIGH_UPPER = 70.00

CRITICAL_KEYWORDS = (
    "critical",
    "no control",
    "unprotected",
    "completely absent",
    "severe",
    "unauthorized",
    "violation",
    "prohibited",
    "no evidence",
    "missing mandatory",
    "breach",
    "zero",
    "fail",
)

HIGH_KEYWORDS = (
    "lacks",
    "missing",
    "fails to",
    "not defined",
    "not implemented",
    "inadequate",
    "absent",
    "no policy",
    "unencrypted",
    "non-compliant",
    "omitted",
)

MEDIUM_KEYWORDS = (
    "partial",
    "incomplete",
    "unclear",
    "ambiguous",
    "inconsistent",
    "procedure",
    "not specified",
    "delay",
    "gap",
    "category",
    "exceptions",
)

LOW_KEYWORDS = (
    "minor",
    "documentation",
    "periodic review",
    "update",
    "formatting",
    "advisory",
    "guideline",
    "clarification",
    "recommended",
)


def classify_gap_text(gap_text: str) -> GapSeverity:
    """Deterministically classify gap text into a severity level."""
    lower = gap_text.lower()
    for kw in CRITICAL_KEYWORDS:
        if kw in lower:
            return GapSeverity.CRITICAL
    for kw in HIGH_KEYWORDS:
        if kw in lower:
            return GapSeverity.HIGH
    for kw in MEDIUM_KEYWORDS:
        if kw in lower:
            return GapSeverity.MEDIUM
    for kw in LOW_KEYWORDS:
        if kw in lower:
            return GapSeverity.LOW
    return GapSeverity.MEDIUM


def determine_risk_level(risk_score: float) -> RiskLevel:
    """Map final normalized risk score deterministically to a risk level."""
    if risk_score < RISK_LEVEL_LOW_UPPER:
        return RiskLevel.LOW
    elif risk_score < RISK_LEVEL_MEDIUM_UPPER:
        return RiskLevel.MEDIUM
    elif risk_score < RISK_LEVEL_HIGH_UPPER:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def calculate_evidence_strength(evidence: list[EvidenceReference]) -> float:
    """Deterministically calculate evidence strength from verified evidence references."""
    if not evidence:
        return 0.0
    total_sim = sum(ref.similarity for ref in evidence)
    avg_sim = total_sim / len(evidence)
    return max(0.0, min(1.0, avg_sim))


def parse_identified_gaps(gaps: list[str | dict[str, Any] | IdentifiedGap]) -> list[IdentifiedGap]:
    """Deterministically normalize gaps into structured IdentifiedGap objects."""
    identified: list[IdentifiedGap] = []
    for g in gaps:
        if isinstance(g, IdentifiedGap):
            identified.append(g)
        elif isinstance(g, dict):
            desc = g.get("description", str(g))
            sev = g.get("severity")
            if sev and str(sev).upper() in GAP_SEVERITY_MAPPING:
                identified.append(
                    IdentifiedGap(description=desc, severity=GapSeverity(str(sev).upper()))
                )
            else:
                identified.append(IdentifiedGap(description=desc, severity=classify_gap_text(desc)))
        elif isinstance(g, str):
            identified.append(IdentifiedGap(description=g, severity=classify_gap_text(g)))
        else:
            desc = str(g)
            identified.append(IdentifiedGap(description=desc, severity=classify_gap_text(desc)))
    return identified


def generate_risk_explanation(
    risk_score: float,
    risk_level: RiskLevel,
    compliance_status: str,
    compliance_contribution: float,
    regulatory_criticality: str,
    regulatory_contribution: float,
    identified_gaps: list[IdentifiedGap],
    gap_contribution: float,
    evidence_strength: float,
    evidence_contribution: float,
    confidence: float,
    confidence_contribution: float,
) -> str:
    """Generate a deterministic, auditor-ready explanation of the calculated risk."""
    lines: list[str] = [
        f"Assessed compliance risk score is {risk_score:.2f} ({risk_level.value})."
    ]

    if compliance_status == "INSUFFICIENT_EVIDENCE":
        lines.append(
            f"Compliance status is INSUFFICIENT_EVIDENCE contributing "
            f"{compliance_contribution:.2f} points (weight 40%). Lack of policy evidence "
            "introduces inherent compliance uncertainty, as absence of evidence cannot be "
            "treated as compliant."
        )
    else:
        lines.append(
            f"Compliance status is {compliance_status} contributing "
            f"{compliance_contribution:.2f} points (weight 40%)."
        )

    lines.append(
        f"Regulatory requirement criticality is {regulatory_criticality} contributing "
        f"{regulatory_contribution:.2f} points (weight 20%)."
    )

    if identified_gaps:
        max_gap_sev = max(
            GAP_SEVERITY_MAPPING[g.severity.value] for g in identified_gaps
        )
        lines.append(
            f"Identified {len(identified_gaps)} gap(s) with maximum severity {max_gap_sev:.2f}, "
            f"contributing {gap_contribution:.2f} points (weight 15%)."
        )
    else:
        lines.append(
            "No policy gaps were identified, contributing "
            f"{gap_contribution:.2f} points (weight 15%)."
        )

    lines.append(
        f"Average verified evidence similarity is {evidence_strength:.2f}, contributing "
        f"{evidence_contribution:.2f} points (weight 15%). "
        f"Step 2B model confidence is {confidence:.2f}, contributing "
        f"{confidence_contribution:.2f} points (weight 10%)."
    )

    return " ".join(lines)


class ComplianceRiskScoringService:
    """Deterministic compliance risk scoring engine (Step 3).

    Consumes verified Step 2B compliance analyses and evaluates compliance risk
    using transparent weighted business rules. Never calls an LLM or performs
    additional vector searches.
    """

    def __init__(
        self,
        compliance_analysis_service: ComplianceAnalysisService,
        db_session: Session | None = None,
        *,
        settings: Settings | None = None,
    ) -> None:
        self.compliance_analysis_service = compliance_analysis_service
        self.db = db_session
        self.settings = settings or get_settings()

    def calculate_risk(
        self,
        *,
        compliance_status: str,
        confidence: float,
        evidence: list[EvidenceReference],
        gaps: list[str | dict[str, Any] | IdentifiedGap],
        regulatory_criticality: str = "MEDIUM",
    ) -> tuple[float, RiskLevel, RiskFactorBreakdown, list[IdentifiedGap], str]:
        """Pure deterministic risk calculation method without database dependencies.

        Args:
            compliance_status: COMPLIANT, PARTIALLY_COMPLIANT, NON_COMPLIANT, or
                INSUFFICIENT_EVIDENCE.
            confidence: Float between 0.0 and 1.0.
            evidence: List of verified Step 2B EvidenceReference objects.
            gaps: Identified gaps (strings or structured).
            regulatory_criticality: LOW, MEDIUM, HIGH, or CRITICAL.

        Returns:
            Tuple of (risk_score, risk_level, factor_breakdown, identified_gaps, explanation).
        """
        # 1. Validation
        if confidence < 0.0 or confidence > 1.0:
            raise ValidationError(f"Confidence must be between 0.0 and 1.0, got {confidence}")

        status_key = compliance_status.upper()
        if status_key not in COMPLIANCE_SEVERITY_MAPPING:
            raise ValidationError(
                f"Invalid compliance status '{compliance_status}'. Expected one of: "
                f"{list(COMPLIANCE_SEVERITY_MAPPING.keys())}"
            )

        crit_key = regulatory_criticality.upper()
        if crit_key not in REGULATORY_CRITICALITY_MAPPING:
            raise ValidationError(
                f"Invalid regulatory criticality '{regulatory_criticality}'. Expected one of: "
                f"{list(REGULATORY_CRITICALITY_MAPPING.keys())}"
            )

        # 2. Factor values
        compliance_val = COMPLIANCE_SEVERITY_MAPPING[status_key]
        criticality_val = REGULATORY_CRITICALITY_MAPPING[crit_key]

        identified_gaps = parse_identified_gaps(gaps)
        if identified_gaps:
            gap_val = max(GAP_SEVERITY_MAPPING[g.severity.value] for g in identified_gaps)
        else:
            gap_val = 0.0

        evidence_val = calculate_evidence_strength(evidence)
        confidence_val = confidence

        # 3. Weights
        w_comp = self.settings.risk_weight_compliance_severity
        w_crit = self.settings.risk_weight_regulatory_criticality
        w_gap = self.settings.risk_weight_gap_severity
        w_ev = self.settings.risk_weight_evidence_strength
        w_conf = self.settings.risk_weight_confidence

        # 4. Contributions
        contrib_comp = round(compliance_val * w_comp * 100.0, 2)
        contrib_crit = round(criticality_val * w_crit * 100.0, 2)
        contrib_gap = round(gap_val * w_gap * 100.0, 2)
        contrib_ev = round(evidence_val * w_ev * 100.0, 2)
        contrib_conf = round(confidence_val * w_conf * 100.0, 2)

        # 5. Final Score
        raw_score = contrib_comp + contrib_crit + contrib_gap + contrib_ev + contrib_conf
        risk_score = max(0.0, min(100.0, round(raw_score, 2)))

        # 6. Risk Level
        risk_level = determine_risk_level(risk_score)

        # 7. Factor Breakdown
        breakdown = RiskFactorBreakdown(
            compliance_severity=RiskFactorDetail(
                value=compliance_val,
                weight=w_comp,
                contribution=contrib_comp,
                description=f"Status {status_key} mapped to severity {compliance_val:.2f}.",
            ),
            regulatory_criticality=RiskFactorDetail(
                value=criticality_val,
                weight=w_crit,
                contribution=contrib_crit,
                description=(
                    f"Regulatory clause criticality {crit_key} mapped to {criticality_val:.2f}."
                ),
            ),
            gap_severity=RiskFactorDetail(
                value=gap_val,
                weight=w_gap,
                contribution=contrib_gap,
                description=(
                    f"Maximum gap severity {gap_val:.2f} across {len(identified_gaps)} gap(s)."
                    if identified_gaps
                    else "No identified gaps."
                ),
            ),
            evidence_strength=RiskFactorDetail(
                value=evidence_val,
                weight=w_ev,
                contribution=contrib_ev,
                description=f"Average verified evidence similarity is {evidence_val:.2f}.",
            ),
            confidence=RiskFactorDetail(
                value=confidence_val,
                weight=w_conf,
                contribution=contrib_conf,
                description=f"Step 2B analysis confidence is {confidence_val:.2f}.",
            ),
        )

        # 8. Explanation
        explanation = generate_risk_explanation(
            risk_score=risk_score,
            risk_level=risk_level,
            compliance_status=status_key,
            compliance_contribution=contrib_comp,
            regulatory_criticality=crit_key,
            regulatory_contribution=contrib_crit,
            identified_gaps=identified_gaps,
            gap_contribution=contrib_gap,
            evidence_strength=evidence_val,
            evidence_contribution=contrib_ev,
            confidence=confidence_val,
            confidence_contribution=contrib_conf,
        )

        return risk_score, risk_level, breakdown, identified_gaps, explanation

    def score_from_analysis(
        self,
        analysis: ComplianceAnalysisResponse,
        clause: Clause | None = None,
        regulatory_criticality: str | None = None,
    ) -> RiskScoringResponse:
        """Compute RiskScoringResponse from a verified Step 2B ComplianceAnalysisResponse."""
        if regulatory_criticality is not None:
            crit = regulatory_criticality
        elif clause is not None:
            crit = getattr(clause, "effective_criticality", "MEDIUM")
        else:
            crit = self.settings.default_regulatory_criticality

        risk_score, risk_level, breakdown, identified_gaps, explanation = self.calculate_risk(
            compliance_status=analysis.compliance_status,
            confidence=analysis.confidence,
            evidence=analysis.evidence,
            gaps=analysis.gaps,
            regulatory_criticality=crit,
        )

        return RiskScoringResponse(
            organization_id=analysis.organization_id,
            regulatory_clause_id=analysis.regulatory_clause_id,
            compliance_status=analysis.compliance_status,
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=analysis.confidence,
            factor_breakdown=breakdown,
            identified_gaps=identified_gaps,
            explanation=explanation,
        )

    def evaluate_risk(
        self,
        organization_id: UUID,
        regulatory_clause_id: UUID,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> RiskScoringResponse:
        """Execute full compliance risk assessment pipeline.

        1. Validates organization and regulatory clause existence.
        2. Retrieves clause criticality.
        3. Invokes Step 2B ComplianceAnalysisService (reusing Step 2A and tenant isolation).
        4. Calculates deterministic risk score and breakdown.
        5. Persists assessment to DB if database session available.
        6. Logs structured audit telemetry without exposing sensitive data.
        7. Returns structured RiskScoringResponse.
        """
        start_time = time.perf_counter()

        # 1. Organization validation
        if self.db is not None:
            org = self.db.get(Organization, organization_id)
            if not org:
                raise NotFoundError("Organization", str(organization_id))

            # 2. Clause lookup
            stmt = select(Clause).where(Clause.id == regulatory_clause_id)
            clause = self.db.scalars(stmt).unique().one_or_none()
            if not clause:
                raise NotFoundError("Regulatory clause", str(regulatory_clause_id))
            criticality = clause.effective_criticality
        else:
            clause = None
            criticality = self.settings.default_regulatory_criticality

        # 3. Step 2B Compliance Analysis (reuses Step 2A matching + pgvector)
        analysis_response = self.compliance_analysis_service.analyze(
            organization_id=organization_id,
            regulatory_clause_id=regulatory_clause_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        # 4. Deterministic Risk Scoring
        response = self.score_from_analysis(
            analysis=analysis_response,
            clause=clause,
            regulatory_criticality=criticality,
        )

        # 5. Persistence
        if self.db is not None:
            assessment_record = ComplianceRiskAssessment(
                organization_id=organization_id,
                regulatory_clause_id=regulatory_clause_id,
                risk_score=response.risk_score,
                risk_level=response.risk_level.value,
                compliance_status=response.compliance_status,
                confidence=response.confidence,
                factor_breakdown=response.factor_breakdown.model_dump(mode="json"),
                identified_gaps=[g.model_dump(mode="json") for g in response.identified_gaps],
                explanation=response.explanation,
            )
            self.db.add(assessment_record)
            self.db.commit()
            self.db.refresh(assessment_record)
            response.id = assessment_record.id
            response.created_at = assessment_record.created_at

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "Compliance risk assessment completed organization_id={} regulatory_clause_id={} "
            "compliance_status={} risk_score={} risk_level={} confidence={} latency_ms={}",
            organization_id,
            regulatory_clause_id,
            response.compliance_status,
            response.risk_score,
            response.risk_level.value,
            response.confidence,
            latency_ms,
        )

        return response
