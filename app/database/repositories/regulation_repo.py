"""Regulation repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.repositories.base import BaseRepository
from app.models.regulation import Regulation, RegulationVersion


class RegulationRepository(BaseRepository[Regulation]):
  def __init__(self, session: Session) -> None:
    super().__init__(session, Regulation)

  def list_all(self, skip: int = 0, limit: int = 50) -> list[Regulation]:
    stmt = select(Regulation).offset(skip).limit(limit)
    return list(self.session.scalars(stmt).all())

  def get_current_version(self, regulation_id) -> RegulationVersion | None:
    stmt = select(RegulationVersion).where(
      RegulationVersion.regulation_id == regulation_id,
      RegulationVersion.is_current.is_(True),
    )
    return self.session.scalar(stmt)
