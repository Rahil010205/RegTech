"""Regulatory Clause model."""

from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

EMBEDDING_DIMENSION = 1024


class Clause(Base):
    """Atomic regulatory requirement extracted from a regulation version."""

    __tablename__ = "clauses"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    version_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("regulation_versions.id"), nullable=False)
    clause_number: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    text: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    qdrant_point_id: Mapped[UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", postgresql.JSONB(), server_default="{}")
    section: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    page_number: Mapped[int | None] = mapped_column(sa.Integer(), nullable=True)
    page_end: Mapped[int | None] = mapped_column(sa.Integer(), nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=True)
    criticality: Mapped[str] = mapped_column(sa.String(20), server_default="MEDIUM", default="MEDIUM")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    version: Mapped["RegulationVersion"] = relationship("RegulationVersion", back_populates="clauses")

    @property
    def effective_criticality(self) -> str:
        return self.criticality or "MEDIUM"
