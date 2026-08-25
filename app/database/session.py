"""Database session factory."""

from collections.abc import Generator

import app.models  # noqa: F401 — register all ORM mappers
from sqlalchemy.orm import Session, sessionmaker

from app.database.engine import create_db_engine

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session, None, None]:
  """Yield a database session; close on exit."""
  session = SessionLocal()
  try:
    yield session
  finally:
    session.close()
