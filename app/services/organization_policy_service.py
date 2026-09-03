"""Organization policy upload, ingestion, and search service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.organization_document import (
    OrganizationCreateRequest,
    OrganizationDocumentIngestResponse,
    OrganizationPolicySearchHit,
    OrganizationPolicySearchResponse,
    OrganizationResponse,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.ingestion.embedding_service import EmbeddingService
from app.ingestion.organization_policy_pipeline import OrganizationPolicyPipeline
from app.models.organization import Organization
from app.retrieval.organization_vector_search import OrganizationPolicyVectorSearch
from app.retrieval.query_embedding import QueryEmbeddingService


class OrganizationPolicyService:
    def __init__(
        self,
        db: Session,
        *,
        settings: Settings | None = None,
        pipeline: OrganizationPolicyPipeline | None = None,
        query_embedder: QueryEmbeddingService | None = None,
        vector_search: OrganizationPolicyVectorSearch | None = None,
    ) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.pipeline = pipeline or OrganizationPolicyPipeline(db)
        self.query_embedder = query_embedder or QueryEmbeddingService(EmbeddingService())
        self.vector_search = vector_search or OrganizationPolicyVectorSearch(db)

    def create_organization(self, payload: OrganizationCreateRequest) -> OrganizationResponse:
        existing = self.db.scalars(
            select(Organization).where(Organization.slug == payload.slug)
        ).one_or_none()
        if existing is not None:
            raise ValidationError(
                f"Organization slug '{payload.slug}' already exists",
                details={"slug": payload.slug},
            )
        organization = Organization(name=payload.name, slug=payload.slug)
        self.db.add(organization)
        self.db.commit()
        self.db.refresh(organization)
        return OrganizationResponse(id=organization.id, name=organization.name, slug=organization.slug)

    def get_organization(self, organization_id: UUID) -> OrganizationResponse:
        organization = self._require_organization(organization_id)
        return OrganizationResponse(id=organization.id, name=organization.name, slug=organization.slug)

    def upload_document(
        self,
        *,
        organization_id: UUID,
        filename: str,
        content: bytes,
        document_type: str | None,
        version: str | None,
    ) -> OrganizationDocumentIngestResponse:
        self._require_organization(organization_id)
        result = self.pipeline.ingest_upload(
            organization_id=organization_id,
            filename=filename,
            content=content,
            document_type=document_type,
            version=version,
        )
        return OrganizationDocumentIngestResponse(
            document_id=result.document_id,
            organization_id=result.organization_id,
            document_name=result.document_name,
            status=result.status,
            chunks_created=result.chunks_created,
            error=result.error,
        )

    def search(
        self,
        *,
        organization_id: UUID,
        query: str,
        top_k: int | None = None,
        min_similarity: float | None = None,
    ) -> OrganizationPolicySearchResponse:
        self._require_organization(organization_id)
        effective_top_k = top_k or self.settings.retrieval_top_k
        if effective_top_k < 1 or effective_top_k > self.settings.retrieval_top_k_max:
            raise ValidationError(
                f"top_k must be between 1 and {self.settings.retrieval_top_k_max}",
                details={"top_k": effective_top_k},
            )

        query_embedding = self.query_embedder.embed_query(query)
        rows = self.vector_search.search(
            query_embedding,
            organization_id=organization_id,
            top_k=effective_top_k,
            min_similarity=min_similarity,
        )
        results = [
            OrganizationPolicySearchHit(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                document_name=row.document_name,
                content=row.content,
                section_title=row.section_title,
                clause_reference=row.clause_reference,
                similarity=round(row.similarity, 4),
                metadata=row.metadata,
            )
            for row in rows
        ]
        return OrganizationPolicySearchResponse(
            query=query,
            organization_id=organization_id,
            results=results,
            total_results=len(results),
        )

    def _require_organization(self, organization_id: UUID) -> Organization:
        organization = self.db.get(Organization, organization_id)
        if organization is None:
            raise NotFoundError("Organization", str(organization_id))
        return organization
