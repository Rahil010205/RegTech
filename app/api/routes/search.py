"""Semantic clause search endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_search_service
from app.api.schemas.search import RetrievalRequest, RetrievalResponse
from app.services.search_service import SearchService

router = APIRouter()


@router.post(
    "",
    response_model=RetrievalResponse,
    summary="Semantic search over regulatory clauses",
    description=(
        "Convert a natural-language compliance question into an embedding and "
        "retrieve the most similar regulatory clauses from PostgreSQL/pgvector."
    ),
)
async def search_regulatory_clauses(
    request: RetrievalRequest,
    service: Annotated[SearchService, Depends(get_search_service)],
) -> RetrievalResponse:
    """Search ingested regulatory clauses by semantic similarity."""
    return service.search_clauses(
        query=request.query,
        top_k=request.top_k,
        filters=request.filters,
        min_similarity=request.min_similarity,
    )
