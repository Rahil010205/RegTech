"""Vector similarity search."""

from typing import Any

from app.vectordb.qdrant_client import get_qdrant_client


class VectorSearch:
  """Semantic search with payload filtering."""

  def search(
    self,
    collection: str,
    query_vector: list[float],
    top_k: int = 10,
    filters: dict[str, Any] | None = None,
  ) -> list[dict[str, Any]]:
    """Search collection. Implementation pending."""
    raise NotImplementedError
