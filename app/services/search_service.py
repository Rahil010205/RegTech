"""Search/retrieval application service."""

from sqlalchemy.orm import Session

from app.retrieval.retriever import Retriever
from app.retrieval.schemas import RetrievalFilters, RetrievalResponse


class SearchService:
    """Application service for semantic regulatory clause search."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.retriever = Retriever(db)

    def search_clauses(
        self,
        query: str,
        top_k: int | None = None,
        filters: RetrievalFilters | None = None,
        min_similarity: float | None = None,
    ) -> RetrievalResponse:
        return self.retriever.retrieve(
            query=query,
            top_k=top_k,
            filters=filters,
            min_similarity=min_similarity,
        )
