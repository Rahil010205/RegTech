"""Compliance Risk Assessment model."""

from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ComplianceRiskAssessment(Base):
    """Compliance risk evaluation record linking a regulatory clause to an organization's policies."""

    __tablename__ = "compliance_risk_assessments"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    regulatory_clause_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("clauses.id", ondelete="CASCADE"), nullable=False)
    compliance_analysis_id: Mapped[UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), nullable=True)
    risk_score: Mapped[float] = mapped_column(sa.Float(), nullable=False)
    risk_level: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    compliance_status: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(sa.Float(), nullable=False)
    factor_breakdown: Mapped[dict] = mapped_column(postgresql.JSONB(), server_default="{}", default=dict)
    identified_gaps: Mapped[list] = mapped_column(postgresql.JSONB(), server_default="[]", default=list)
    explanation: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), default=datetime.utcnow)
