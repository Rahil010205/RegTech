"""Integration tests for Step 2B LLM-based compliance analysis with real pgvector and embeddings."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.api.schemas.compliance_analysis import (
    ComplianceAnalysisResult,
    EvidenceReference,
)
from app.core.constants import JobStatus, OrganizationDocumentStatus
from app.ingestion.embedding_service import EmbeddingService
from app.models.clause import Clause
from app.models.organization import Organization
from app.models.organization_document import OrganizationDocument
from app.models.organization_policy_chunk import OrganizationPolicyChunk
from app.models.regulation import Regulation, RegulationVersion, Regulator
from app.services.compliance_analysis import ComplianceAnalysisService
from app.services.llm.client import MockLLMClient
from app.services.regulatory_policy_matching import RegulatoryPolicyMatchingService


IDENTITY_CLAUSE = (
    "The regulated entity shall identify and verify the identity of customers "
    "before establishing a business relationship."
)
POLICY_IDENTITY = (
    "The company shall identify and verify every customer before establishing a business relationship."
)
POLICY_STATIONERY = "The office stationery procurement process shall be approved by administration."
POLICY_ORG_A = "Our company verifies customer identity before account opening."
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
    regulator = Regulator(code=regulator_code, name="Compliance Test Regulator", jurisdiction="IN")
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
        version=f"comp-{suffix}",
        content_hash=f"comp-hash-{suffix}",
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
    org = Organization(name=f"Comp Org {suffix}", slug=f"comp-org-{suffix}")
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


def test_compliance_analysis_with_real_pgvector_and_mock_llm(db_session: Session) -> None:
    embedder = EmbeddingService()
    reg = _seed_regulation(db_session, embedder, IDENTITY_CLAUSE)
    org, doc = _seed_org_with_chunks(
        db_session,
        embedder,
        [
            (POLICY_IDENTITY, "Customer Identification", "1.1"),
            (POLICY_STATIONERY, "Procurement", "9.1"),
        ],
    )

    try:
        matching_service = RegulatoryPolicyMatchingService(db_session, embedding_service=embedder)

        def mock_llm_handler(system_prompt: str, user_prompt: str, response_schema):
            # Assert that untrusted data guidance and regulatory text reached LLM
            assert "UNTRUSTED" in system_prompt or "UNTRUSTED" in user_prompt
            assert "The regulated entity shall identify and verify" in user_prompt
            assert "The company shall identify and verify every customer" in user_prompt

            # Find chunk id for POLICY_IDENTITY
            chunk = (
                db_session.query(OrganizationPolicyChunk)
                .filter_by(organization_id=org.id, section_title="Customer Identification")
                .one()
            )
            return ComplianceAnalysisResult(
                compliance_status="COMPLIANT",
                confidence=0.92,
                reasoning="The policy directly implements customer identification and verification.",
                evidence=[
                    EvidenceReference(
                        chunk_id=chunk.id,
                        document_id=doc.id,
                        similarity=0.90,
                        relevance="supports",
                        explanation="Explicitly mandates customer verification before onboarding.",
                    )
                ],
                gaps=[],
            )

        mock_llm = MockLLMClient(response_provider=mock_llm_handler)
        compliance_service = ComplianceAnalysisService(
            matching_service=matching_service,
            llm_client=mock_llm,
        )

        response = compliance_service.analyze(
            organization_id=org.id,
            regulatory_clause_id=reg["clause_id"],
            top_k=5,
            similarity_threshold=0.60,
        )

        assert response.compliance_status == "COMPLIANT"
        assert response.confidence == 0.92
        assert len(response.evidence) == 1
        assert response.evidence[0].document_id == doc.id
        assert response.gaps == []
        assert len(mock_llm.calls) == 1
    finally:
        _cleanup(
            db_session,
            org_ids=[org.id],
            version_id=reg["version_id"],
            regulation_id=reg["regulation_id"],
            regulator_code=reg["regulator_code"],
        )


def test_compliance_analysis_organization_isolation(db_session: Session) -> None:
    embedder = EmbeddingService()
    reg = _seed_regulation(db_session, embedder, IDENTITY_CLAUSE)
    org_a, _ = _seed_org_with_chunks(
        db_session,
        embedder,
        [(POLICY_ORG_A, "Identification", "1.0")],
    )
    org_b, _ = _seed_org_with_chunks(
        db_session,
        embedder,
        [(POLICY_STATIONERY, "Office Supplies", "2.0")],
    )

    try:
        matching_service = RegulatoryPolicyMatchingService(db_session, embedding_service=embedder)
        mock_llm = MockLLMClient()
        compliance_service = ComplianceAnalysisService(
            matching_service=matching_service,
            llm_client=mock_llm,
        )

        # For Org B, only stationery chunk exists. At threshold 0.70, no chunks should match.
        response = compliance_service.analyze(
            organization_id=org_b.id,
            regulatory_clause_id=reg["clause_id"],
            top_k=5,
            similarity_threshold=0.70,
        )

        assert response.compliance_status == "INSUFFICIENT_EVIDENCE"
        assert response.confidence == 0.0
        assert response.evidence == []
        # LLM must not be called when no evidence exists
        assert len(mock_llm.calls) == 0
    finally:
        _cleanup(
            db_session,
            org_ids=[org_a.id, org_b.id],
            version_id=reg["version_id"],
            regulation_id=reg["regulation_id"],
            regulator_code=reg["regulator_code"],
        )


def test_compliance_analysis_no_evidence_does_not_call_llm(db_session: Session) -> None:
    embedder = EmbeddingService()
    # Seed cybersecurity clause
    reg = _seed_regulation(db_session, embedder, CYBER_CLAUSE)
    # Seed policy containing only stationery
    org, _ = _seed_org_with_chunks(
        db_session,
        embedder,
        [(POLICY_STATIONERY, "Admin", "1.0")],
    )

    try:
        matching_service = RegulatoryPolicyMatchingService(db_session, embedding_service=embedder)
        mock_llm = MockLLMClient()
        compliance_service = ComplianceAnalysisService(
            matching_service=matching_service,
            llm_client=mock_llm,
        )

        response = compliance_service.analyze(
            organization_id=org.id,
            regulatory_clause_id=reg["clause_id"],
            top_k=5,
            similarity_threshold=0.70,
        )

        assert response.compliance_status == "INSUFFICIENT_EVIDENCE"
        assert response.confidence == 0.0
        assert response.evidence == []
        assert response.gaps == ["No relevant organization policy evidence was retrieved."]
        assert len(mock_llm.calls) == 0
    finally:
        _cleanup(
            db_session,
            org_ids=[org.id],
            version_id=reg["version_id"],
            regulation_id=reg["regulation_id"],
            regulator_code=reg["regulator_code"],
        )
