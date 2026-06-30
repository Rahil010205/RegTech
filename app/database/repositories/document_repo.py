"""Document repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.repositories.base import BaseRepository
from app.models.document import Document


class DocumentRepository(BaseRepository[Document]):
  def __init__(self, session: Session) -> None:
    super().__init__(session, Document)

  def list_by_org(self, org_id: UUID, skip: int = 0, limit: int = 50) -> list[Document]:
    stmt = select(Document).where(Document.org_id == org_id).offset(skip).limit(limit)
    return list(self.session.scalars(stmt).all())
