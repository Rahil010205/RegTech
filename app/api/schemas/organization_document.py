"""API schemas for organization policy documents."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)

    @field_validator("name", "slug")
    @classmethod
    def strip_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Value cannot be empty")
        return stripped


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str


class OrganizationDocumentIngestResponse(BaseModel):
    document_id: UUID
    organization_id: UUID
    document_name: str | None = None
    status: str
    chunks_created: int = 0
    error: str | None = None


class OrganizationPolicySearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    min_similarity: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("query")
    @classmethod
    def validate_query_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Query cannot be empty")
        return value.strip()


class OrganizationPolicySearchHit(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_name: str | None = None
    content: str
    section_title: str | None = None
    clause_reference: str | None = None
    similarity: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class OrganizationPolicySearchResponse(BaseModel):
    query: str
    organization_id: UUID
    results: list[OrganizationPolicySearchHit]
    total_results: int
