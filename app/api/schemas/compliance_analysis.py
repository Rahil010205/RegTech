"""Schemas for LLM-based regulatory compliance analysis (Step 2B)."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ComplianceStatus = Literal[
    "COMPLIANT",
    "PARTIALLY_COMPLIANT",
    "NON_COMPLIANT",
    "INSUFFICIENT_EVIDENCE",
]

EvidenceRelevance = Literal[
    "supports",
    "partially_supports",
    "contradicts",
]


class ComplianceAnalysisRequest(BaseModel):
    """Request payload for compliance analysis."""

    regulatory_clause_id: UUID = Field(
        ...,
        description="UUID of the regulatory clause to evaluate against organization policies.",
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
        description="Minimum cosine similarity threshold for policy evidence (0.0 to 1.0).",
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


class EvidenceReference(BaseModel):
    """A referenced organization policy chunk providing evidence for compliance status."""

    chunk_id: UUID = Field(
        ...,
        description="UUID of the policy chunk.",
    )
    document_id: UUID = Field(
        ...,
        description="UUID of the parent organization document.",
    )
    similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score between regulatory clause and policy chunk from Step 2A.",
    )
    relevance: EvidenceRelevance = Field(
        ...,
        description="Whether this chunk supports, partially supports, or contradicts compliance.",
    )
    explanation: str = Field(
        ...,
        description="Specific explanation of how this policy chunk relates to the requirement.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
                "document_id": "c1a0e2dd-5b43-4a90-8fd5-c601637e0740",
                "similarity": 0.91,
                "relevance": "supports",
                "explanation": "Directly addresses customer identification and verification before onboarding.",
            }
        }
    )


class ComplianceAnalysisResult(BaseModel):
    """Structured LLM analysis output representation."""

    compliance_status: ComplianceStatus = Field(
        ...,
        description=(
            "Classification status: COMPLIANT (clearly addresses requirement), "
            "PARTIALLY_COMPLIANT (addressed but gaps/ambiguity exist), "
            "NON_COMPLIANT (contradicts or explicitly lacks required control), "
            "INSUFFICIENT_EVIDENCE (insufficient evidence to determine)."
        ),
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Model's confidence in the compliance classification based on the provided evidence. "
            "Note: This does not represent probability of legal compliance, a risk score, or legal certainty."
        ),
    )
    reasoning: str = Field(
        ...,
        description="Concise decision rationale explaining regulatory requirement, policy content, and alignment.",
    )
    evidence: list[EvidenceReference] = Field(
        default_factory=list,
        description="Referenced policy chunks that support, partially support, or contradict the finding.",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Identified gaps or missing controls derived strictly from the requirement and evidence.",
    )


class ComplianceAnalysisResponse(BaseModel):
    """Complete API response for compliance analysis."""

    organization_id: UUID = Field(
        ...,
        description="Organization identifier.",
    )
    regulatory_clause_id: UUID = Field(
        ...,
        description="Regulatory clause identifier evaluated.",
    )
    compliance_status: ComplianceStatus = Field(
        ...,
        description="Determined compliance status.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in analysis (0.0 - 1.0).",
    )
    reasoning: str = Field(
        ...,
        description="Concise decision rationale.",
    )
    evidence: list[EvidenceReference] = Field(
        default_factory=list,
        description="Policy evidence references.",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Material gaps or deficiencies identified.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "organization_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                "regulatory_clause_id": "b1b17b2b-0331-419b-b9f0-cbeaf9da19f9",
                "compliance_status": "PARTIALLY_COMPLIANT",
                "confidence": 0.87,
                "reasoning": (
                    "The regulatory clause requires customer identification and verification before establishing "
                    "the business relationship. The organization's KYC policy explicitly requires customer identification "
                    "and verification during onboarding, which directly addresses the requirement. However, the retrieved "
                    "evidence does not specify the required verification procedure for all customer categories."
                ),
                "evidence": [
                    {
                        "chunk_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
                        "document_id": "c1a0e2dd-5b43-4a90-8fd5-c601637e0740",
                        "similarity": 0.91,
                        "relevance": "supports",
                        "explanation": "Explicitly mandates customer identification prior to account opening.",
                    }
                ],
                "gaps": [
                    "Policy does not specify the verification procedure for all customer categories.",
                ],
            }
        }
    )
