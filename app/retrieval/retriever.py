"""Top-K semantic clause retriever."""

from app.core.constants import COLLECTION_REGULATORY_CLAUSES  # ← ADD THIS IMPORT
from app.embeddings.embedding_generator import EmbeddingGenerator
from app.vectordb.search import VectorSearch


class Retriever:
    """Retrieve relevant regulatory clauses for a document section."""

    def __init__(self) -> None:
        self.embedder = EmbeddingGenerator()
        self.search = VectorSearch()

    def retrieve(
        self,
        query_text: str,
        regulator_codes: list[str],
        top_k: int = 10,
    ) -> list[dict]:
        """Retrieve top-K relevant clauses."""
        # Generate query embedding
        query_vector = self.embedder.embed_query(query_text)
        
        # Build filters
        filters = {"regulator": regulator_codes} if regulator_codes else None
        
        # Search Qdrant
        return self.search.search(
            collection=COLLECTION_REGULATORY_CLAUSES,
            query_vector=query_vector,
            top_k=top_k,
            filters=filters,
        )