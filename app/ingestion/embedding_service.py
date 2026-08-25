"""Embedding generation service with pluggable providers."""

from __future__ import annotations

from typing import Protocol

from loguru import logger

from app.core.config import Settings, get_settings
from app.core.exceptions import EmbeddingModelError


class EmbeddingProvider(Protocol):
    """Port for embedding backends (local model, OpenAI, etc.)."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    @property
    def embedding_dimension(self) -> int:
        ...


class LocalEmbeddingProvider:
    """Sentence-transformers provider using the configured BGE model."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        from app.embeddings.embedding_generator import EmbeddingGenerator

        self._generator = EmbeddingGenerator()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        try:
            return self._generator.embed_texts(texts)
        except Exception as exc:
            logger.error("Local embedding generation failed: {}", exc)
            raise EmbeddingModelError(f"Local embedding generation failed: {exc}") from exc

    def embed_query(self, query: str) -> list[float]:
        """Embed a retrieval query using the BGE query prefix."""
        try:
            return self._generator.embed_query(query)
        except Exception as exc:
            logger.error("Local query embedding failed: {}", exc)
            raise EmbeddingModelError(f"Local query embedding failed: {exc}") from exc

    @property
    def embedding_dimension(self) -> int:
        return self._generator.embedding_dim


class OpenAIEmbeddingProvider:
    """OpenAI embeddings API provider."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        if not self._settings.openai_api_key:
            raise EmbeddingModelError("OpenAI API key is not configured")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise EmbeddingModelError(
                "openai package is required for OpenAI embedding provider"
            ) from exc

        self._client = OpenAI(api_key=self._settings.openai_api_key)
        self._model = self._settings.openai_embedding_model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self._client.embeddings.create(model=self._model, input=texts)
            return [item.embedding for item in response.data]
        except Exception as exc:
            logger.error("OpenAI embedding generation failed: {}", exc)
            raise EmbeddingModelError(f"OpenAI embedding generation failed: {exc}") from exc

    @property
    def embedding_dimension(self) -> int:
        if "large" in self._model:
            return 3072
        if "3-small" in self._model:
            return 1536
        return get_settings().embedding_dimension


class EmbeddingService:
    """Application-facing embedding service used by the ingestion pipeline."""

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._provider = provider or self._build_provider()

    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding for a single clause/document text."""
        vectors = self.embed_texts([text])
        return vectors[0]

    def embed_query(self, query: str) -> list[float]:
        """Generate an embedding for a retrieval query.

        Uses BGE query-prefix conventions for the local provider so query
        vectors remain compatible with ingested clause embeddings.
        """
        if hasattr(self._provider, "embed_query"):
            return self._provider.embed_query(query)
        return self.embed_text(query)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in provider-native batches."""
        if not texts:
            return []
        logger.info("Generating embeddings for {} text(s)", len(texts))
        return self._provider.embed_texts(texts)

    @property
    def embedding_dimension(self) -> int:
        return self._provider.embedding_dimension

    def _build_provider(self) -> EmbeddingProvider:
        provider_name = self._settings.embedding_provider.lower().strip()
        if provider_name == "openai":
            return OpenAIEmbeddingProvider(self._settings)
        if provider_name == "local":
            return LocalEmbeddingProvider(self._settings)
        raise EmbeddingModelError(f"Unsupported embedding provider: {provider_name}")
