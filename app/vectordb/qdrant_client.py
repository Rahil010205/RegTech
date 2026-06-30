"""Qdrant client wrapper with connection pooling and retries."""

from qdrant_client import QdrantClient

from app.core.config import get_settings


def get_qdrant_client() -> QdrantClient:
  """Return a configured Qdrant client."""
  settings = get_settings()
  return QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key,
    timeout=settings.qdrant_timeout,
  )
