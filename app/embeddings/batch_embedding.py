"""Batch embedding with configurable chunk size and progress logging.

Designed to handle thousands of clauses without running out of memory by
processing them in fixed-size batches and logging progress periodically.
"""

from __future__ import annotations

import logging
import math
from typing import TypedDict

from app.embeddings.embedding_generator import EmbeddingGenerator

logger = logging.getLogger(__name__)


class EmbeddedClause(TypedDict):
    """A clause record enriched with its embedding vector."""

    text: str
    embedding: list[float]


class BatchEmbedder:
    """Embed large collections of clause texts efficiently.

    Args:
        batch_size: Number of texts sent to the model per call (default 32).
        log_every:  Log a progress line every *N* batches (default every 5).
    """

    def __init__(self, batch_size: int = 32, log_every: int = 5) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        self.batch_size = batch_size
        self.log_every = log_every
        self.generator = EmbeddingGenerator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_all(self, texts: list[str]) -> list[list[float]]:
        """Embed all texts, processing them in batches.

        Args:
            texts: List of clause text strings.

        Returns:
            List of 1024-dimensional float vectors in the same order as
            the input *texts*.
        """
        if not texts:
            logger.warning("BatchEmbedder.embed_all called with empty list")
            return []

        total = len(texts)
        n_batches = math.ceil(total / self.batch_size)
        logger.info(
            "Starting batch embedding: %d texts, batch_size=%d → %d batches",
            total,
            self.batch_size,
            n_batches,
        )

        all_vectors: list[list[float]] = []

        for batch_idx in range(n_batches):
            start = batch_idx * self.batch_size
            end = min(start + self.batch_size, total)
            batch = texts[start:end]

            vectors = self.generator.embed_texts(batch)
            all_vectors.extend(vectors)

            # Progress log every N batches and on the last batch
            if (batch_idx + 1) % self.log_every == 0 or (batch_idx + 1) == n_batches:
                pct = ((batch_idx + 1) / n_batches) * 100
                logger.info(
                    "  Batch %d/%d (%.0f%%) — embedded %d/%d texts",
                    batch_idx + 1,
                    n_batches,
                    pct,
                    len(all_vectors),
                    total,
                )

        logger.info("Batch embedding complete: %d vectors produced", len(all_vectors))
        return all_vectors

    def embed_clause_records(self, records: list[dict]) -> list[EmbeddedClause]:
        """Embed a list of clause dicts (as produced by the ingestion pipeline).

        Extracts the ``"text"`` field from each record, embeds all texts in
        batches, then returns a list of ``{"text": ..., "embedding": [...]}``
        dicts ready for Qdrant insertion.

        Args:
            records: List of clause dicts; each must have a ``"text"`` key.

        Returns:
            List of :class:`EmbeddedClause` dicts.

        Raises:
            KeyError: If any record is missing the ``"text"`` key.
        """
        texts = [r["text"] for r in records]
        vectors = self.embed_all(texts)
        return [
            EmbeddedClause(text=text, embedding=vec)
            for text, vec in zip(texts, vectors, strict=True)
        ]
