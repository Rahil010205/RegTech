"""Singleton loader for BAAI/bge-large-en-v1.5."""


class ModelLoader:
  """Lazy-load and cache the sentence-transformers embedding model."""

  _instance = None
  _model = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def get_model(self):
    """Load model on first call. Implementation pending."""
    raise NotImplementedError
