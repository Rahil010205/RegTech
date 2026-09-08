"""Legacy / base Document models."""

from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Document(Base):
    """Document uploaded for compliance processing."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False)
    filename: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    doc_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), server_default="pending")
    content_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(sa.String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    sections: Mapped[list["DocumentSection"]] = relationship("DocumentSection", back_populates="document", cascade="all, delete-orphan")


class DocumentSection(Base):
    """Extracted text section of a document."""

    __tablename__ = "document_sections"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False)
    section_number: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    text: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    document: Mapped["Document"] = relationship("Document", back_populates="sections")
