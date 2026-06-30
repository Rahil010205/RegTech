"""Generic repository base class."""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
  """Base CRUD operations for ORM models."""

  def __init__(self, session: Session, model: type[ModelT]) -> None:
    self.session = session
    self.model = model

  def get_by_id(self, entity_id: UUID) -> ModelT | None:
    return self.session.get(self.model, entity_id)

  def add(self, entity: ModelT) -> ModelT:
    self.session.add(entity)
    self.session.flush()
    return entity

  def delete(self, entity: ModelT) -> None:
    self.session.delete(entity)
    self.session.flush()
