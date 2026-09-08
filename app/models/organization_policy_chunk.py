"""Organization Policy Chunk model with pgvector."""

from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

EMBEDDING_DIMENSION = 1024


class OrganizationPolicyChunk(Base):
    """Chunk of an internal policy document with vector embedding."""

    __tablename__ = "organization_policy_chunks"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("organization_documents.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    section_title: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    clause_reference: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    content: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", postgresql.JSONB(), server_default="{}")
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    document: Mapped["OrganizationDocument"] = relationship("OrganizationDocument", back_populates="chunks")
