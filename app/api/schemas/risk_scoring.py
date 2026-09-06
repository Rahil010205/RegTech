"""Schemas for deterministic compliance risk scoring and severity assessment (Step 3)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.compliance_analysis import ComplianceStatus


class GapSeverity(StrEnum):
    """Gap severity classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskLevel(StrEnum):
    """Normalized compliance risk level classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IdentifiedGap(BaseModel):
    """Structured gap representation with deterministic severity classification."""

    description: str = Field(
        ...,
        description="Text description of the identified gap or missing control.",
    )
    severity: GapSeverity = Field(
        ...,
        description="Classified severity of this gap (LOW, MEDIUM, HIGH, CRITICAL).",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": (
                    "Policy does not specify verification procedures for high-risk customers."
                ),
                "severity": "HIGH",
            }
        }
    )


class RiskFactorDetail(BaseModel):
    """Detailed breakdown for an individual risk factor."""

    value: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized factor input value between 0.0 and 1.0.",
    )
    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Configured factor weight in the scoring model (e.g. 0.40).",
    )
    contribution: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Weighted contribution of this factor to the final 0–100 risk score.",
    )
    description: str | None = Field(
        default=None,
        description="Human-readable explanation of this factor's input and contribution.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "value": 1.0,
                "weight": 0.40,
                "contribution": 40.0,
                "description": "NON_COMPLIANT status carries maximum compliance severity.",
            }
        }
    )


class RiskFactorBreakdown(BaseModel):
    """Explainable breakdown of all 5 deterministic risk factors."""

    compliance_severity: RiskFactorDetail = Field(
        ...,
        description="Compliance status severity contribution (40% weight).",
    )
    regulatory_criticality: RiskFactorDetail = Field(
        ...,
        description="Regulatory clause criticality contribution (20% weight).",
    )
    gap_severity: RiskFactorDetail = Field(
        ...,
        description="Identified gaps severity contribution (15% weight).",
    )
    evidence_strength: RiskFactorDetail = Field(
        ...,
        description="Policy evidence strength and similarity contribution (15% weight).",
    )
    confidence: RiskFactorDetail = Field(
        ...,
        description="Step 2B model confidence factor contribution (10% weight).",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "compliance_severity": {
                    "value": 1.0,
                    "weight": 0.40,
                    "contribution": 40.0,
                    "description": "NON_COMPLIANT status maps to 1.00 severity.",
                },
                "regulatory_criticality": {
                    "value": 0.75,
                    "weight": 0.20,
                    "contribution": 15.0,
                    "description": "Regulatory clause criticality is HIGH (0.75).",
                },
                "gap_severity": {
                    "value": 0.75,
                    "weight": 0.15,
                    "contribution": 11.25,
                    "description": "Maximum identified gap severity is HIGH (0.75).",
                },
                "evidence_strength": {
                    "value": 0.80,
                    "weight": 0.15,
                    "contribution": 12.0,
                    "description": "Average verified evidence similarity is 0.80.",
                },
                "confidence": {
                    "value": 0.80,
                    "weight": 0.10,
                    "contribution": 8.0,
                    "description": "Step 2B analysis confidence is 0.80.",
                },
            }
        }
    )


class RiskScoringRequest(BaseModel):
    """Request payload for compliance risk assessment."""

    regulatory_clause_id: UUID = Field(
        ...,
        description="UUID of the regulatory clause to assess risk for.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of policy chunks to retrieve via Step 2A semantic matching (1 to 50).",
    )
    similarity_threshold: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity cutoff for policy evidence (0.0 to 1.0).",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "regulatory_clause_id": "b1b17b2b-0331-419b-b9f0-cbeaf9da19f9",
                "top_k": 5,
                "similarity_threshold": 0.60,
            }
        }
    )


class RiskScoringResponse(BaseModel):
    """Complete, transparent, and auditable risk scoring assessment response."""

    id: UUID | None = Field(
        default=None,
        description="Persistent assessment record UUID (if persisted).",
    )
    organization_id: UUID = Field(
        ...,
        description="Organization identifier evaluated.",
    )
    regulatory_clause_id: UUID = Field(
        ...,
        description="Regulatory clause identifier evaluated.",
    )
    compliance_status: ComplianceStatus = Field(
        ...,
        description="Input compliance status determined by Step 2B.",
    )
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Final normalized deterministic risk score (0.00 to 100.00).",
    )
    risk_level: RiskLevel = Field(
        ...,
        description=(
            "Classified risk level: LOW (<20), MEDIUM (20-39.99), HIGH (40-69.99), "
            "CRITICAL (>=70)."
        ),
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Analysis confidence from Step 2B (0.0 to 1.0).",
    )
    factor_breakdown: RiskFactorBreakdown = Field(
        ...,
        description=(
            "Transparent factor breakdown explaining exact weights, values, and contributions."
        ),
    )
    identified_gaps: list[IdentifiedGap] = Field(
        default_factory=list,
        description="Identified compliance gaps with individual classified severities.",
    )
    explanation: str = Field(
        ...,
        description=(
            "Auditor-ready deterministic narrative explaining why this risk level was assigned."
        ),
    )
    created_at: datetime | None = Field(
        default=None,
        description="Timestamp when the risk assessment was created.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "organization_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                "regulatory_clause_id": "b1b17b2b-0331-419b-b9f0-cbeaf9da19f9",
                "compliance_status": "NON_COMPLIANT",
                "risk_score": 86.25,
                "risk_level": "CRITICAL",
                "confidence": 0.80,
                "factor_breakdown": {
                    "compliance_severity": {
                        "value": 1.0,
                        "weight": 0.40,
                        "contribution": 40.0,
                    },
                    "regulatory_criticality": {
                        "value": 0.75,
                        "weight": 0.20,
                        "contribution": 15.0,
                    },
                    "gap_severity": {
                        "value": 0.75,
                        "weight": 0.15,
                        "contribution": 11.25,
                    },
                    "evidence_strength": {
                        "value": 0.80,
                        "weight": 0.15,
                        "contribution": 12.0,
                    },
                    "confidence": {
                        "value": 0.80,
                        "weight": 0.10,
                        "contribution": 8.0,
                    },
                },
                "identified_gaps": [
                    {
                        "description": (
                            "Policy completely lacks mandatory customer verification controls."
                        ),
                        "severity": "CRITICAL",
                    }
                ],
                "explanation": (
                    "Assessed compliance risk score is 86.25 (CRITICAL). "
                    "Status NON_COMPLIANT contributes 40.00 points (weight 40%). "
                    "Regulatory clause criticality is HIGH (0.75), contributing 15.00 "
                    "points (weight 20%). "
                    "Identified gaps have maximum severity CRITICAL (1.00), contributing "
                    "11.25 points (weight 15%). "
                    "Average verified evidence similarity is 0.80, contributing 12.00 points "
                    "(weight 15%). "
                    "Step 2B confidence is 0.80, contributing 8.00 points (weight 10%)."
                ),
            }
        }
    )
