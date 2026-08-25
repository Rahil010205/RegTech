"""Retrieval domain schemas."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RetrievalFilters(BaseModel):
    """Optional metadata filters supported by the current schema."""

    regulator: str | None = Field(default=None, description="Regulator code, e.g. RBI")
    jurisdiction: str | None = Field(default=None, description="Jurisdiction code, e.g. IN")
    document_id: UUID | None = Field(
        default=None,
        description="Regulation version ID (document version identifier)",
    )
    document_type: str | None = None
    section: str | None = None
    effective_date: date | None = None
    clause_number: str | None = None


class RetrievedClause(BaseModel):
    """A clause returned by semantic search."""

    clause_id: UUID
    document_id: UUID
    document_name: str | None = None
    regulator: str | None = None
    clause_number: str | None = None
    section: str | None = None
    text: str
    page_number: int | None = None
    similarity: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalRequest(BaseModel):
    """Input payload for semantic clause retrieval."""

    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    min_similarity: float | None = Field(default=None, ge=0.0, le=1.0)
    filters: RetrievalFilters | None = None

    @field_validator("query")
    @classmethod
    def validate_query_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Query cannot be empty")
        return value.strip()


class RetrievalResponse(BaseModel):
    """Output payload for semantic clause retrieval."""

    query: str
    top_k: int
    min_similarity: float | None = None
    results: list[RetrievedClause]
    total_results: int
