"""Regulation models."""

from datetime import date, datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Regulator(Base):
    """Regulatory authority (e.g. RBI, SEBI, IRDAI)."""

    __tablename__ = "regulators"

    code: Mapped[str] = mapped_column(sa.String(20), primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(sa.String(50), nullable=False)


class Regulation(Base):
    """Global regulatory document issued by an authority."""

    __tablename__ = "regulations"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    regulator_code: Mapped[str] = mapped_column(sa.String(20), sa.ForeignKey("regulators.code"), nullable=False)
    title: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    document_type: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="CIRCULAR")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    versions: Mapped[list["RegulationVersion"]] = relationship(back_populates="regulation", cascade="all, delete-orphan")


class RegulationVersion(Base):
    """Specific version of a regulatory document."""

    __tablename__ = "regulation_versions"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    regulation_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("regulations.id"), nullable=False)
    version: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="1.0")
    effective_date: Mapped[date | None] = mapped_column(sa.Date(), nullable=True)
    is_current: Mapped[bool] = mapped_column(sa.Boolean(), server_default=sa.false())
    content_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), server_default="pending")
    storage_path: Mapped[str | None] = mapped_column(sa.String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    regulation: Mapped["Regulation"] = relationship(back_populates="versions")
    clauses: Mapped[list["Clause"]] = relationship("Clause", back_populates="version", cascade="all, delete-orphan")
