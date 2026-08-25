"""Semantic retrieval module."""

from app.retrieval.query_embedding import QueryEmbeddingService
from app.retrieval.retriever import Retriever, search_clauses
from app.retrieval.schemas import RetrievedClause, RetrievalFilters, RetrievalRequest, RetrievalResponse
from app.retrieval.vector_search import VectorSearchService

__all__ = [
    "QueryEmbeddingService",
    "Retriever",
    "RetrievedClause",
    "RetrievalFilters",
    "RetrievalRequest",
    "RetrievalResponse",
    "VectorSearchService",
    "search_clauses",
]
