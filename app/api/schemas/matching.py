"""Schemas for regulatory clause → organization policy matching."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class RegulatoryPolicyMatchRequest(BaseModel):
    regulatory_clause_id: UUID
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.60, ge=0.0, le=1.0)


class MatchedRegulatoryClause(BaseModel):
    id: UUID
    reference: str | None = None
    content: str
    section: str | None = None
    title: str | None = None
    regulation_name: str | None = None
    regulator: str | None = None
    version: str | None = None
    effective_date: date | None = None


class RegulatoryPolicyMatchHit(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_name: str | None = None
    document_type: str | None = None
    document_version: str | None = None
    content: str
    section_title: str | None = None
    clause_reference: str | None = None
    similarity: float
    rank: int


class RegulatoryPolicyMatchResponse(BaseModel):
    organization_id: UUID
    regulatory_clause_id: UUID
    top_k: int
    similarity_threshold: float
    total_results: int
    regulatory_clause: MatchedRegulatoryClause
    results: list[RegulatoryPolicyMatchHit]
