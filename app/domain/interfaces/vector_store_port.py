"""Vector store port."""

from typing import Any, Protocol
from uuid import UUID


class VectorStorePort(Protocol):
  """Abstract interface for vector database operations."""

  def upsert_points(
    self,
    collection: str,
    ids: list[UUID],
    vectors: list[list[float]],
    payloads: list[dict[str, Any]],
  ) -> None:
    """Upsert vectors with metadata payloads."""
    ...

  def search(
    self,
    collection: str,
    query_vector: list[float],
    top_k: int,
    filters: dict[str, Any] | None = None,
  ) -> list[dict[str, Any]]:
    """Semantic search with optional payload filters."""
    ...
