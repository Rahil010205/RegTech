"""Organization Document model."""

from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OrganizationDocument(Base):
    """Internal policy or SOP uploaded by an organization."""

    __tablename__ = "organization_documents"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False)
    document_name: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    document_type: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    source_filename: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    version: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="PROCESSING")
    error_message: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    chunks: Mapped[list["OrganizationPolicyChunk"]] = relationship("OrganizationPolicyChunk", back_populates="document", cascade="all, delete-orphan")
