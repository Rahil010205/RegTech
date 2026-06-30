"""Single and query embedding generation."""

from app.core.constants import BGE_QUERY_PREFIX
from app.embeddings.model_loader import ModelLoader


class EmbeddingGenerator:
  """Generate embeddings using BGE-large-en-v1.5."""

  def __init__(self) -> None:
    self._loader = ModelLoader()

  def embed_texts(self, texts: list[str]) -> list[list[float]]:
    """Embed document texts. Implementation pending."""
    raise NotImplementedError

  def embed_query(self, query: str) -> list[float]:
    """Embed a search query with BGE query prefix. Implementation pending."""
    prefixed = f"{BGE_QUERY_PREFIX}{query}"
    return self.embed_texts([prefixed])[0]
