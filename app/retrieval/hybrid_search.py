"""Dense + sparse hybrid search."""


class HybridSearch:
  """Combine vector search with metadata/BM25 filtering."""

  def search(self, query: str, filters: dict, top_k: int = 10) -> list[dict]:
    """Hybrid search. Implementation pending."""
    raise NotImplementedError
