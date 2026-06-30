"""Batch vector upsert to Qdrant."""

from typing import Any
from uuid import UUID

from app.vectordb.qdrant_client import get_qdrant_client


class VectorUploader:
  """Upload clause embeddings to Qdrant with idempotency."""

  def upsert(
    self,
    collection: str,
    ids: list[UUID],
    vectors: list[list[float]],
    payloads: list[dict[str, Any]],
  ) -> None:
    """Batch upsert points. Implementation pending."""
    raise NotImplementedError
