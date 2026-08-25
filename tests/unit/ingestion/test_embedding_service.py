"""Tests for EmbeddingService."""

from app.ingestion.embedding_service import EmbeddingService, LocalEmbeddingProvider


class _FakeProvider:
    embedding_dimension = 4

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 0.0, 0.0, 1.0] for text in texts]


class TestEmbeddingService:
    def test_embed_text_returns_single_vector(self) -> None:
        service = EmbeddingService(provider=_FakeProvider())
        vector = service.embed_text("sample clause")
        assert vector == [13.0, 0.0, 0.0, 1.0]

    def test_embed_texts_preserves_order(self) -> None:
        service = EmbeddingService(provider=_FakeProvider())
        vectors = service.embed_texts(["aa", "bbb"])
        assert vectors[0][0] == 2.0
        assert vectors[1][0] == 3.0

    def test_local_provider_is_constructable(self) -> None:
        provider = LocalEmbeddingProvider()
        assert provider.embedding_dimension == 1024
