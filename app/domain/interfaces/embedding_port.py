"""Embedding generation port."""

from typing import Protocol


class EmbeddingPort(Protocol):
  """Abstract interface for text embedding generation."""

  def embed_texts(self, texts: list[str]) -> list[list[float]]:
    """Embed a batch of document texts."""
    ...

  def embed_query(self, query: str) -> list[float]:
    """Embed a single search query."""
    ...
