"""Batch embedding with memory-aware chunking."""

from app.embeddings.embedding_generator import EmbeddingGenerator


class BatchEmbedder:
  """Process large clause sets in configurable batches."""

  def __init__(self, batch_size: int = 32) -> None:
    self.batch_size = batch_size
    self.generator = EmbeddingGenerator()

  def embed_all(self, texts: list[str]) -> list[list[float]]:
    """Embed all texts in batches. Implementation pending."""
    raise NotImplementedError
