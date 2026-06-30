"""Database session dependency."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database.session import get_session


def get_db() -> Generator[Session, None, None]:
  """FastAPI dependency that yields a SQLAlchemy session."""
  yield from get_session()
