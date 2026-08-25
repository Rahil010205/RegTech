"""Repository for regulatory clause persistence."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.clause import Clause


class ClauseRepository:
    """Data access for clause records and embeddings."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def delete_by_version(self, version_id: UUID) -> int:
        """Remove all clauses for a version (used before re-ingestion)."""
        result = self.session.execute(delete(Clause).where(Clause.version_id == version_id))
        self.session.flush()
        return result.rowcount or 0

    def bulk_create(self, clauses: list[Clause]) -> list[Clause]:
        """Persist a batch of clause ORM objects."""
        self.session.add_all(clauses)
        self.session.flush()
        return clauses

    def count_by_version(self, version_id: UUID) -> int:
        stmt = select(Clause.id).where(Clause.version_id == version_id)
        return len(self.session.scalars(stmt).all())

    def list_by_version(self, version_id: UUID, limit: int = 10) -> list[Clause]:
        stmt = select(Clause).where(Clause.version_id == version_id).limit(limit)
        return list(self.session.scalars(stmt).all())
