"""Singleton loader for BAAI/bge-large-en-v1.5.

Loads the sentence-transformers model exactly once per process and caches
it for all subsequent callers.  Thread-safe via Python's GIL for the
initial load; the singleton is set before the object is returned, so
concurrent first-callers may both load the model but only one instance
will be stored (harmless race).
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_MODEL_NAME = os.environ.get("REGTECH_EMBEDDING_MODEL_NAME", "BAAI/bge-large-en-v1.5")
_DEVICE = os.environ.get("REGTECH_EMBEDDING_DEVICE", "cpu")


class ModelLoader:
    """Lazy-load and cache the BGE large English embedding model.

    Usage::

        model = ModelLoader().get_model()
        embeddings = model.encode(["some text"])
    """

    _instance: ModelLoader | None = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> ModelLoader:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self) -> SentenceTransformer:
        """Return the cached model, loading it on the first call.

        The model is loaded from HuggingFace Hub or local cache.
        Subsequent calls return the already-loaded instance instantly.

        Returns:
            A :class:`sentence_transformers.SentenceTransformer` instance
            for ``BAAI/bge-large-en-v1.5`` (1024-dimensional outputs).
        """
        if self._model is None:
            logger.info(
                "Loading embedding model '%s' on device='%s' …", _MODEL_NAME, _DEVICE
            )
            from sentence_transformers import SentenceTransformer  # lazy import

            self._model = SentenceTransformer(_MODEL_NAME, device=_DEVICE)
            logger.info("Embedding model loaded ✓  (dim=%d)", self.embedding_dim)

        return self._model

    @property
    def embedding_dim(self) -> int:
        """Return the vector dimensionality (1024 for bge-large-en-v1.5)."""
        if self._model is not None:
            return self._model.get_sentence_embedding_dimension()
        return 1024  # known constant for this model
