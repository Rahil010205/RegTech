"""Compliance repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.repositories.base import BaseRepository
from app.models.compliance_run import ComplianceFinding, ComplianceRun


class ComplianceRepository(BaseRepository[ComplianceRun]):
  def __init__(self, session: Session) -> None:
    super().__init__(session, ComplianceRun)

  def get_findings(self, run_id: UUID) -> list[ComplianceFinding]:
    stmt = select(ComplianceFinding).where(ComplianceFinding.run_id == run_id)
    return list(self.session.scalars(stmt).all())
