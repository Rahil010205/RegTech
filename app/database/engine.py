"""SQLAlchemy engine factory."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.core.config import get_settings


def create_db_engine() -> Engine:
  """Create a SQLAlchemy engine with connection pooling."""
  settings = get_settings()
  return create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
  )
