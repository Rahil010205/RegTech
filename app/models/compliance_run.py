"""Compliance run, finding, ingestion job, and report models."""

from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class IngestionJob(Base):
    """Background ingestion task."""

    __tablename__ = "ingestion_jobs"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), server_default="pending")
    error_message: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    error_code: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())


class ComplianceRun(Base):
    """Compliance assessment execution run."""

    __tablename__ = "compliance_runs"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False)
    document_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), server_default="pending")
    risk_score: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    compliance_pct: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    findings: Mapped[list["ComplianceFinding"]] = relationship("ComplianceFinding", back_populates="run", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="run", cascade="all, delete-orphan")


class ComplianceFinding(Base):
    """Individual clause compliance finding."""

    __tablename__ = "compliance_findings"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("compliance_runs.id"), nullable=False)
    clause_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("clauses.id"), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(30), nullable=False)
    severity: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    gap_description: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    evidence: Mapped[dict] = mapped_column(postgresql.JSONB(), server_default="{}")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    run: Mapped["ComplianceRun"] = relationship("ComplianceRun", back_populates="findings")


class Report(Base):
    """Generated compliance report."""

    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("compliance_runs.id"), nullable=False)
    format: Mapped[str] = mapped_column(sa.String(10), nullable=False)
    storage_path: Mapped[str] = mapped_column(sa.String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    run: Mapped["ComplianceRun"] = relationship("ComplianceRun", back_populates="reports")
