"""Audit log model."""

from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    """System audit trail for compliance and tracking."""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id: Mapped[UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True)
    action: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True)
    payload: Mapped[dict] = mapped_column(postgresql.JSONB(), server_default="{}")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
