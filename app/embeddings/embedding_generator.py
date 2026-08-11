"""Single and batch embedding generation using BGE-large-en-v1.5.

The BGE models require a query prefix for retrieval queries but no prefix
for documents being indexed — this module handles both cases.
"""

from __future__ import annotations

import logging

import numpy as np

from app.core.constants import BGE_QUERY_PREFIX
from app.embeddings.model_loader import ModelLoader

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate semantic embeddings using BAAI/bge-large-en-v1.5.

    Attributes:
        _loader: Shared :class:`ModelLoader` singleton.
    """

    def __init__(self) -> None:
        self._loader = ModelLoader()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of document texts.

        Args:
            texts: Non-empty list of text strings to embed.

        Returns:
            List of 1024-dimensional float vectors, one per input text.

        Raises:
            ValueError: If ``texts`` is empty.
        """
        if not texts:
            raise ValueError("embed_texts: 'texts' must be a non-empty list")

        model = self._loader.get_model()
        logger.debug("Embedding %d text(s) …", len(texts))

        vectors: np.ndarray = model.encode(
            texts,
            normalize_embeddings=True,   # recommended for BGE cosine similarity
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        # Convert to plain Python floats for JSON-serializability
        return [vec.tolist() for vec in vectors]

    def embed_query(self, query: str) -> list[float]:
        """Embed a search query with the required BGE query prefix.

        The BGE models are trained to prepend
        ``"Represent this sentence for searching relevant passages: "``
        to retrieval queries (but NOT to indexed documents).

        Args:
            query: Raw user query string.

        Returns:
            1024-dimensional float vector.
        """
        prefixed = f"{BGE_QUERY_PREFIX}{query}"
        logger.debug("Embedding query (length=%d) …", len(prefixed))
        return self.embed_texts([prefixed])[0]

    @property
    def embedding_dim(self) -> int:
        """Expected output dimensionality (1024 for bge-large-en-v1.5)."""
        return self._loader.embedding_dim
