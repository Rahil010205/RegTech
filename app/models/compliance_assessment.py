"""Persistent record for document-level, clause-by-clause compliance assessments."""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ComplianceAssessment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "compliance_assessments"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "policy_document_id",
            "policy_clause_id",
            "regulatory_clause_id",
            name="uq_compliance_assessment_pair",
        ),
        Index("ix_compliance_assessment_org_doc", "organization_id", "policy_document_id"),
        Index("ix_compliance_assessment_doc_policy", "policy_document_id", "policy_clause_id"),
        Index("ix_compliance_assessment_reg_clause", "regulatory_clause_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organization_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_clause_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organization_policy_chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    regulatory_clause_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clauses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matching_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="NOT_DETERMINABLE")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    policy_evidence: Mapped[str] = mapped_column(Text, nullable=False, default="")
    regulatory_requirement: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reasoning_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    analysis_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank: Mapped[int | None] = mapped_column(nullable=True)

    organization = relationship("Organization")
    policy_document = relationship("OrganizationDocument")
    policy_clause = relationship("OrganizationPolicyChunk")
    regulatory_clause = relationship("Clause")
