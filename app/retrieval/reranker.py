"""Cross-encoder or score-fusion reranking."""


class Reranker:
  """Rerank retrieved clauses by relevance."""

  def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank candidates. Implementation pending."""
    raise NotImplementedError
