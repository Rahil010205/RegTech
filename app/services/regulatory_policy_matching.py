"""Match a regulatory clause to organization policy chunks via pgvector."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.schemas.matching import (
    MatchedRegulatoryClause,
    RegulatoryPolicyMatchHit,
    RegulatoryPolicyMatchResponse,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import EmbeddingModelError, NotFoundError, ValidationError
from app.ingestion.embedding_service import EmbeddingService
from app.models.clause import EMBEDDING_DIMENSION, Clause
from app.models.organization import Organization
from app.models.regulation import Regulation, RegulationVersion
from app.retrieval.organization_vector_search import OrganizationPolicyVectorSearch


class RegulatoryPolicyMatchingService:
    """Retrieve organization-policy evidence for a single regulatory clause.

    This service does not decide compliance. It only ranks semantically
    similar policy chunks for later analysis.
    """

    def __init__(
        self,
        session: Session,
        *,
        settings: Settings | None = None,
        embedding_service: EmbeddingService | None = None,
        vector_search: OrganizationPolicyVectorSearch | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_search = vector_search or OrganizationPolicyVectorSearch(session)

    def match_regulatory_clause_to_policy(
        self,
        organization_id: UUID,
        regulatory_clause_id: UUID,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> RegulatoryPolicyMatchResponse:
        effective_top_k = top_k if top_k is not None else self.settings.retrieval_top_k
        effective_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else self.settings.matching_similarity_threshold
        )
        self._validate_params(effective_top_k, effective_threshold)
        self._require_organization(organization_id)

        logger.info(
            "Regulatory-policy matching started organization_id={} regulatory_clause_id={}",
            organization_id,
            regulatory_clause_id,
        )

        clause = self._load_clause(regulatory_clause_id)
        embedding = self._resolve_clause_embedding(clause)
        logger.info("Retrieved regulatory clause embedding")

        logger.info("Searching organization policy chunks")
        try:
            rows = self.vector_search.search(
                embedding,
                organization_id=organization_id,
                top_k=effective_top_k,
                min_similarity=effective_threshold,
            )
        except ValueError as exc:
            raise EmbeddingModelError(str(exc)) from exc
        logger.info("Candidate policy chunks retrieved: {}", len(rows))

        results = [
            RegulatoryPolicyMatchHit(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                document_name=row.document_name,
                document_type=row.document_type,
                document_version=row.document_version,
                content=row.content,
                section_title=row.section_title,
                clause_reference=row.clause_reference,
                similarity=round(row.similarity, 4),
                rank=index,
            )
            for index, row in enumerate(rows, start=1)
        ]
        logger.info("Results above similarity threshold: {}", len(results))
        logger.info("Regulatory-policy matching completed")

        return RegulatoryPolicyMatchResponse(
            organization_id=organization_id,
            regulatory_clause_id=regulatory_clause_id,
            top_k=effective_top_k,
            similarity_threshold=effective_threshold,
            total_results=len(results),
            regulatory_clause=self._clause_payload(clause),
            results=results,
        )

    def _validate_params(self, top_k: int, similarity_threshold: float) -> None:
        if top_k < 1 or top_k > self.settings.retrieval_top_k_max:
            raise ValidationError(
                f"top_k must be between 1 and {self.settings.retrieval_top_k_max}",
                details={"top_k": top_k},
            )
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValidationError(
                "similarity_threshold must be between 0.0 and 1.0",
                details={"similarity_threshold": similarity_threshold},
            )

    def _require_organization(self, organization_id: UUID) -> Organization:
        organization = self.session.get(Organization, organization_id)
        if organization is None:
            raise NotFoundError("Organization", str(organization_id))
        return organization

    def _load_clause(self, clause_id: UUID) -> Clause:
        stmt = (
            select(Clause)
            .options(
                joinedload(Clause.version)
                .joinedload(RegulationVersion.regulation)
                .joinedload(Regulation.regulator)
            )
            .where(Clause.id == clause_id)
        )
        clause = self.session.scalars(stmt).unique().one_or_none()
        if clause is None:
            raise NotFoundError("Regulatory clause", str(clause_id))
        return clause

    def _resolve_clause_embedding(self, clause: Clause) -> list[float]:
        stored = clause.embedding
        if stored is not None and len(stored) > 0:
            vector = [float(value) for value in stored]
            self._assert_dimension(vector, source="stored regulatory clause")
            return vector

        logger.info(
            "Regulatory clause embedding missing — generating document embedding clause_id={}",
            clause.id,
        )
        vector = self.embedding_service.embed_text(clause.text)
        self._assert_dimension(vector, source="generated regulatory clause")
        clause.embedding = vector
        self.session.commit()
        return vector

    @staticmethod
    def _assert_dimension(vector: list[float], *, source: str) -> None:
        if len(vector) != EMBEDDING_DIMENSION:
            logger.error(
                "Embedding dimension mismatch source={} actual={} expected={}",
                source,
                len(vector),
                EMBEDDING_DIMENSION,
            )
            raise EmbeddingModelError(
                f"Embedding dimension {len(vector)} does not match expected {EMBEDDING_DIMENSION}"
            )

    @staticmethod
    def _clause_payload(clause: Clause) -> MatchedRegulatoryClause:
        version = clause.version
        regulation = version.regulation if version is not None else None
        regulator = regulation.regulator if regulation is not None else None
        return MatchedRegulatoryClause(
            id=clause.id,
            reference=clause.clause_number,
            content=clause.text,
            section=clause.section,
            title=clause.title,
            regulation_name=regulation.title if regulation is not None else None,
            regulator=regulator.code if regulator is not None else None,
            version=version.version if version is not None else None,
            effective_date=version.effective_date if version is not None else None,
        )
