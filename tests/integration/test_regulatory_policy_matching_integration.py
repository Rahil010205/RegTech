"""Integration tests for regulatory clause → organization policy matching."""

from __future__ import annotations

from uuid import uuid4

import app.models  # noqa: F401
import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.constants import JobStatus, OrganizationDocumentStatus
from app.ingestion.embedding_service import EmbeddingService
from app.models.clause import Clause
from app.models.organization import Organization
from app.models.organization_document import OrganizationDocument
from app.models.organization_policy_chunk import OrganizationPolicyChunk
from app.models.regulation import Regulation, RegulationVersion, Regulator
from app.services.regulatory_policy_matching import RegulatoryPolicyMatchingService


IDENTITY_CLAUSE = (
    "The regulated entity shall identify and verify the identity of customers "
    "before establishing a business relationship."
)
POLICY_IDENTITY = (
    "The company shall identify and verify every customer before establishing a business relationship."
)
POLICY_RETENTION = "The company shall maintain records according to its document retention schedule."
POLICY_STATIONERY = "The office stationery procurement process shall be approved by administration."
POLICY_ORG_A = "Our company verifies customer identity before account opening."
POLICY_ORG_B = "Our company performs customer identity verification using approved procedures."
CYBER_CLAUSE = (
    "The regulated entity shall maintain a specific cybersecurity control for "
    "privileged access workstations isolated from customer onboarding."
)


def _cleanup(
    session: Session,
    *,
    org_ids: list,
    version_id=None,
    regulation_id=None,
    regulator_code: str | None = None,
) -> None:
    for org_id in org_ids:
        session.execute(
            delete(OrganizationPolicyChunk).where(
                OrganizationPolicyChunk.organization_id == org_id
            )
        )
        session.execute(
            delete(OrganizationDocument).where(OrganizationDocument.organization_id == org_id)
        )
        session.execute(delete(Organization).where(Organization.id == org_id))
    if version_id is not None:
        session.execute(delete(Clause).where(Clause.version_id == version_id))
        session.execute(delete(RegulationVersion).where(RegulationVersion.id == version_id))
    if regulation_id is not None:
        session.execute(delete(Regulation).where(Regulation.id == regulation_id))
    if regulator_code is not None:
        session.execute(delete(Regulator).where(Regulator.code == regulator_code))
    session.commit()


def _seed_regulation(session: Session, embedder: EmbeddingService, text: str) -> dict:
    suffix = uuid4().hex[:8]
    regulator_code = f"M{suffix[:4].upper()}"
    regulator = Regulator(code=regulator_code, name="Match Test Regulator", jurisdiction="IN")
    session.add(regulator)
    session.flush()
    regulation = Regulation(
        regulator_code=regulator_code,
        title="KYC Master Direction",
        document_type="regulation",
    )
    session.add(regulation)
    session.flush()
    version = RegulationVersion(
        regulation_id=regulation.id,
        version=f"match-{suffix}",
        content_hash=f"match-hash-{suffix}",
        status=JobStatus.COMPLETED.value,
        is_current=True,
    )
    session.add(version)
    session.flush()
    clause = Clause(
        version_id=version.id,
        clause_number="10.2",
        section="Customer Identification",
        title="Identity verification",
        text=text,
        embedding=embedder.embed_text(text),
    )
    session.add(clause)
    session.commit()
    return {
        "regulator_code": regulator_code,
        "regulation_id": regulation.id,
        "version_id": version.id,
        "clause_id": clause.id,
    }


def _seed_org_with_chunks(
    session: Session,
    embedder: EmbeddingService,
    chunks: list[tuple[str, str | None, str | None]],
) -> tuple[Organization, OrganizationDocument]:
    suffix = uuid4().hex[:8]
    org = Organization(name=f"Match Org {suffix}", slug=f"match-org-{suffix}")
    session.add(org)
    session.flush()
    document = OrganizationDocument(
        organization_id=org.id,
        document_name="company_kyc_policy.pdf",
        document_type="KYC_POLICY",
        version="2026.1",
        status=OrganizationDocumentStatus.PROCESSED.value,
    )
    session.add(document)
    session.flush()
    texts = [content for content, _, _ in chunks]
    vectors = embedder.embed_texts(texts)
    models = [
        OrganizationPolicyChunk(
            document_id=document.id,
            organization_id=org.id,
            chunk_index=index,
            section_title=section,
            clause_reference=reference,
            content=content,
            embedding=vector,
            metadata_={"document_type": "KYC_POLICY", "version": "2026.1"},
        )
        for index, ((content, section, reference), vector) in enumerate(
            zip(chunks, vectors, strict=True)
        )
    ]
    session.add_all(models)
    session.commit()
    return org, document


@pytest.mark.integration
@pytest.mark.slow
def test_identity_policy_ranks_above_stationery(db_session: Session) -> None:
    embedder = EmbeddingService()
    seeded = _seed_regulation(db_session, embedder, IDENTITY_CLAUSE)
    org, _document = _seed_org_with_chunks(
        db_session,
        embedder,
        [
            (POLICY_IDENTITY, "Customer Identification", "1.1"),
            (POLICY_RETENTION, "Record Keeping", "3.1"),
            (POLICY_STATIONERY, "Administration", "9.1"),
        ],
    )
    try:
        service = RegulatoryPolicyMatchingService(db_session, embedding_service=embedder)
        response = service.match_regulatory_clause_to_policy(
            org.id,
            seeded["clause_id"],
            top_k=5,
            similarity_threshold=0.20,
        )
        assert response.total_results >= 1
        assert "identify and verify" in response.results[0].content.lower()
        contents = [hit.content for hit in response.results]
        identity_rank = next(i for i, text in enumerate(contents) if "identify and verify" in text.lower())
        stationery_hits = [
            i for i, text in enumerate(contents) if "stationery" in text.lower()
        ]
        if stationery_hits:
            assert identity_rank < stationery_hits[0]
        assert response.results[0].rank == 1
        dumped = response.model_dump()
        assert "embedding" not in dumped
        assert "embedding" not in dumped["results"][0]
    finally:
        _cleanup(
            db_session,
            org_ids=[org.id],
            version_id=seeded["version_id"],
            regulation_id=seeded["regulation_id"],
            regulator_code=seeded["regulator_code"],
        )


@pytest.mark.integration
@pytest.mark.slow
def test_matching_is_isolated_by_organization(db_session: Session) -> None:
    embedder = EmbeddingService()
    seeded = _seed_regulation(db_session, embedder, IDENTITY_CLAUSE)
    org_a, doc_a = _seed_org_with_chunks(
        db_session, embedder, [(POLICY_ORG_A, "Customer Identification", "1.1")]
    )
    org_b, doc_b = _seed_org_with_chunks(
        db_session, embedder, [(POLICY_ORG_B, "Customer Identification", "1.1")]
    )
    try:
        service = RegulatoryPolicyMatchingService(db_session, embedding_service=embedder)
        response = service.match_regulatory_clause_to_policy(
            org_a.id,
            seeded["clause_id"],
            top_k=5,
            similarity_threshold=0.20,
        )
        assert response.total_results >= 1
        assert all(hit.document_id == doc_a.id for hit in response.results)
        assert all(hit.document_id != doc_b.id for hit in response.results)
    finally:
        _cleanup(
            db_session,
            org_ids=[org_a.id, org_b.id],
            version_id=seeded["version_id"],
            regulation_id=seeded["regulation_id"],
            regulator_code=seeded["regulator_code"],
        )


@pytest.mark.integration
@pytest.mark.slow
def test_similarity_threshold_and_top_k(db_session: Session) -> None:
    embedder = EmbeddingService()
    seeded = _seed_regulation(db_session, embedder, IDENTITY_CLAUSE)
    org, _document = _seed_org_with_chunks(
        db_session,
        embedder,
        [
            (POLICY_IDENTITY, "Customer Identification", "1.1"),
            (POLICY_RETENTION, "Record Keeping", "3.1"),
            (POLICY_STATIONERY, "Administration", "9.1"),
        ],
    )
    try:
        service = RegulatoryPolicyMatchingService(db_session, embedding_service=embedder)
        strict = service.match_regulatory_clause_to_policy(
            org.id, seeded["clause_id"], top_k=5, similarity_threshold=0.80
        )
        loose = service.match_regulatory_clause_to_policy(
            org.id, seeded["clause_id"], top_k=5, similarity_threshold=0.20
        )
        assert all(hit.similarity >= 0.80 for hit in strict.results)
        assert loose.total_results >= strict.total_results
        limited = service.match_regulatory_clause_to_policy(
            org.id, seeded["clause_id"], top_k=1, similarity_threshold=0.20
        )
        assert limited.total_results <= 1
    finally:
        _cleanup(
            db_session,
            org_ids=[org.id],
            version_id=seeded["version_id"],
            regulation_id=seeded["regulation_id"],
            regulator_code=seeded["regulator_code"],
        )


@pytest.mark.integration
@pytest.mark.slow
def test_no_relevant_evidence_returns_empty(db_session: Session) -> None:
    embedder = EmbeddingService()
    seeded = _seed_regulation(db_session, embedder, CYBER_CLAUSE)
    org, _document = _seed_org_with_chunks(
        db_session, embedder, [(POLICY_STATIONERY, "Administration", "9.1")]
    )
    try:
        service = RegulatoryPolicyMatchingService(db_session, embedding_service=embedder)
        response = service.match_regulatory_clause_to_policy(
            org.id,
            seeded["clause_id"],
            top_k=5,
            similarity_threshold=0.80,
        )
        assert response.total_results == 0
        assert response.results == []
    finally:
        _cleanup(
            db_session,
            org_ids=[org.id],
            version_id=seeded["version_id"],
            regulation_id=seeded["regulation_id"],
            regulator_code=seeded["regulator_code"],
        )
