"""Schemas for document-level compliance analysis and report retrieval."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentComplianceStatus(StrEnum):
    COMPLIANT = "COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NOT_DETERMINABLE = "NOT_DETERMINABLE"
    NO_RELEVANT_REGULATION_FOUND = "NO_RELEVANT_REGULATION_FOUND"


class DocumentComplianceAssessmentResult(BaseModel):
    assessment_id: UUID | None = None
    policy_clause: dict[str, Any] = Field(default_factory=dict)
    regulatory_clause: dict[str, Any] = Field(default_factory=dict)
    matching_score: float | None = None
    compliance_score: float | None = None
    status: DocumentComplianceStatus = DocumentComplianceStatus.NOT_DETERMINABLE
    explanation: str = ""
    missing_requirements: list[str] = Field(default_factory=list)
    policy_evidence: str = ""
    recommendation: str | None = None
    regulatory_requirement: str | None = None
    created_at: datetime | None = None


class DocumentComplianceSummary(BaseModel):
    total_requirements: int = 0
    compliant_count: int = 0
    partially_compliant_count: int = 0
    non_compliant_count: int = 0
    not_determinable_count: int = 0
    uncovered_count: int = 0


class UncoveredRequirement(BaseModel):
    regulatory_clause_id: UUID | None = None
    regulatory_requirement: str = ""
    reason: str = ""
    severity: str | None = None


class HighRiskFinding(BaseModel):
    regulatory_clause_id: UUID | None = None
    status: DocumentComplianceStatus = DocumentComplianceStatus.NON_COMPLIANT
    compliance_score: float | None = None
    severity: str | None = None
    issue: str = ""
    recommendation: str | None = None


class DocumentComplianceReportResponse(BaseModel):
    report_id: UUID | None = None
    organization_id: UUID
    policy_document_id: UUID
    policy_document_name: str | None = None
    overall_score: float | None = None
    summary: DocumentComplianceSummary = Field(default_factory=DocumentComplianceSummary)
    results: list[DocumentComplianceAssessmentResult] = Field(default_factory=list)
    uncovered_requirements: list[UncoveredRequirement] = Field(default_factory=list)
    high_risk_findings: list[HighRiskFinding] = Field(default_factory=list)
    generated_at: datetime | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class DocumentComplianceRequest(BaseModel):
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.60, ge=0.0, le=1.0)


ComplianceReportResponse = DocumentComplianceReportResponse
