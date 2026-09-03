"""Integration tests for organization policy ingestion and search."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import app.models  # noqa: F401
import fitz
import pytest
from sqlalchemy import delete, text
from sqlalchemy.orm import Session

from app.core.constants import OrganizationDocumentStatus
from app.ingestion.embedding_service import EmbeddingService
from app.ingestion.organization_policy_pipeline import OrganizationPolicyPipeline
from app.models.clause import EMBEDDING_DIMENSION
from app.models.organization import Organization
from app.models.organization_document import OrganizationDocument
from app.models.organization_policy_chunk import OrganizationPolicyChunk
from app.retrieval.organization_vector_search import OrganizationPolicyVectorSearch
from app.retrieval.query_embedding import QueryEmbeddingService
from app.services.organization_policy_service import OrganizationPolicyService


class _FakeEmbeddingService(EmbeddingService):
    def __init__(self, vector: list[float] | None = None) -> None:
        self._vector = vector or ([0.01] * EMBEDDING_DIMENSION)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [list(self._vector) for _ in texts]

    def embed_query(self, query: str) -> list[float]:
        return list(self._vector)

    @property
    def embedding_dimension(self) -> int:
        return EMBEDDING_DIMENSION


def _write_policy_pdf(path: Path, body: str) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), body)
    doc.save(path)
    doc.close()
    return path


def _cleanup_org(session: Session, organization_id) -> None:
    session.execute(
        delete(OrganizationPolicyChunk).where(
            OrganizationPolicyChunk.organization_id == organization_id
        )
    )
    session.execute(
        delete(OrganizationDocument).where(
            OrganizationDocument.organization_id == organization_id
        )
    )
    session.execute(delete(Organization).where(Organization.id == organization_id))
    session.commit()


@pytest.mark.integration
def test_organization_policy_ingest_and_isolation(db_session: Session, tmp_path: Path) -> None:
    org_a = Organization(name="Org A", slug=f"org-a-{uuid4().hex[:8]}")
    org_b = Organization(name="Org B", slug=f"org-b-{uuid4().hex[:8]}")
    db_session.add_all([org_a, org_b])
    db_session.commit()

    pdf_a = _write_policy_pdf(
        tmp_path / "org_a_kyc.pdf",
        "Section 4 — Customer Identification\n"
        "4.2 The organization shall verify customer identity before onboarding.\n",
    )
    pdf_b = _write_policy_pdf(
        tmp_path / "org_b_kyc.pdf",
        "Section 8 — Unrelated Treasury\n"
        "8.1 The organization shall reconcile nostro accounts daily.\n",
    )

    try:
        pipeline_a = OrganizationPolicyPipeline(db_session, embedding_service=_FakeEmbeddingService())
        result_a = pipeline_a.ingest_file(
            organization_id=org_a.id,
            file_path=pdf_a,
            document_type="KYC_POLICY",
            version="2026.1",
        )
        pipeline_b = OrganizationPolicyPipeline(db_session, embedding_service=_FakeEmbeddingService())
        result_b = pipeline_b.ingest_file(
            organization_id=org_b.id,
            file_path=pdf_b,
            document_type="KYC_POLICY",
        )

        assert result_a.status == OrganizationDocumentStatus.PROCESSED.value
        assert result_a.chunks_created >= 1
        assert result_b.status == OrganizationDocumentStatus.PROCESSED.value

        stored = db_session.execute(
            text(
                """
                SELECT COUNT(*) AS total, COUNT(embedding) AS embedded
                FROM organization_policy_chunks
                WHERE organization_id = :org_id
                """
            ),
            {"org_id": str(org_a.id)},
        ).one()
        assert stored.total == stored.embedded
        assert stored.total >= 1

        dims = db_session.execute(
            text(
                """
                SELECT vector_dims(embedding) AS dims
                FROM organization_policy_chunks
                WHERE organization_id = :org_id
                LIMIT 1
                """
            ),
            {"org_id": str(org_a.id)},
        ).scalar_one()
        assert dims == EMBEDDING_DIMENSION

        embedder = _FakeEmbeddingService()
        service_a = OrganizationPolicyService(
            db_session,
            pipeline=pipeline_a,
            query_embedder=QueryEmbeddingService(embedder),
            vector_search=OrganizationPolicyVectorSearch(db_session),
        )
        search_a = service_a.search(
            organization_id=org_a.id,
            query="customer identification",
            top_k=5,
        )
        assert search_a.total_results >= 1
        assert all(str(org_a.id) for _ in search_a.results)
        assert all(hit.document_id == result_a.document_id for hit in search_a.results)

        search_b = service_a.search(
            organization_id=org_b.id,
            query="customer identification",
            top_k=5,
        )
        assert all(hit.document_id == result_b.document_id for hit in search_b.results)
        assert all(hit.document_id != result_a.document_id for hit in search_b.results)
    finally:
        _cleanup_org(db_session, org_a.id)
        _cleanup_org(db_session, org_b.id)


@pytest.mark.integration
def test_failed_ingestion_sets_failed_status(db_session: Session, tmp_path: Path) -> None:
    org = Organization(name="Org Fail", slug=f"org-fail-{uuid4().hex[:8]}")
    db_session.add(org)
    db_session.commit()
    blank = tmp_path / "blank.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(blank)
    doc.close()

    try:
        pipeline = OrganizationPolicyPipeline(db_session, embedding_service=_FakeEmbeddingService())
        result = pipeline.ingest_file(organization_id=org.id, file_path=blank)
        assert result.status == OrganizationDocumentStatus.FAILED.value
        stored = db_session.get(OrganizationDocument, result.document_id)
        assert stored is not None
        assert stored.status == OrganizationDocumentStatus.FAILED.value
        chunks = db_session.execute(
            text("SELECT COUNT(*) FROM organization_policy_chunks WHERE document_id = :id"),
            {"id": str(result.document_id)},
        ).scalar_one()
        assert chunks == 0
    finally:
        _cleanup_org(db_session, org.id)


@pytest.mark.integration
@pytest.mark.slow
def test_real_embeddings_rank_relevant_policy_chunk(db_session: Session, tmp_path: Path) -> None:
    org = Organization(name="Org Real", slug=f"org-real-{uuid4().hex[:8]}")
    db_session.add(org)
    db_session.commit()
    pdf = _write_policy_pdf(
        tmp_path / "kyc_policy.pdf",
        "Section 4 — Customer Identification\n"
        "4.2 The organization shall verify customer identity and official documents "
        "before establishing a business relationship.\n\n"
        "Section 9 — Office Stationery\n"
        "9.1 Printer paper must be reordered when the cabinet is empty.\n",
    )

    try:
        pipeline = OrganizationPolicyPipeline(db_session, embedding_service=EmbeddingService())
        result = pipeline.ingest_file(
            organization_id=org.id,
            file_path=pdf,
            document_type="KYC_POLICY",
        )
        assert result.status == OrganizationDocumentStatus.PROCESSED.value

        service = OrganizationPolicyService(db_session)
        response = service.search(
            organization_id=org.id,
            query="What customer identification and verification procedures are required?",
            top_k=5,
        )
        assert response.total_results >= 1
        assert any("verify customer identity" in hit.content.lower() for hit in response.results[:3])
        assert "verify customer identity" in response.results[0].content.lower()
        assert "printer paper" not in response.results[0].content.lower()
    finally:
        _cleanup_org(db_session, org.id)
