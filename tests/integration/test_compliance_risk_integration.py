"""Integration tests for Step 3 Compliance Risk Scoring & Severity Engine with database persistence."""

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
from app.core.constants import JobStatus, OrganizationDocumentStatus, RiskScoreLevel
from app.ingestion.embedding_service import EmbeddingService
from app.models.clause import Clause
from app.models.compliance_risk_assessment import ComplianceRiskAssessment
from app.models.organization import Organization
from app.models.organization_document import OrganizationDocument
from app.models.organization_policy_chunk import OrganizationPolicyChunk
from app.models.regulation import Regulation, RegulationVersion, Regulator
from app.services.compliance_analysis import ComplianceAnalysisService
from app.services.compliance_risk_scoring import ComplianceRiskScoringService
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
            delete(ComplianceRiskAssessment).where(
                ComplianceRiskAssessment.organization_id == org_id
            )
        )
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


def _seed_regulation(
    session: Session,
    embedder: EmbeddingService,
    text: str,
    criticality: str = "HIGH",
) -> dict:
    suffix = uuid4().hex[:8]
    regulator_code = f"M{suffix[:4].upper()}"
    regulator = Regulator(code=regulator_code, name="Risk Test Regulator", jurisdiction="IN")
    session.add(regulator)
    session.flush()
    regulation = Regulation(
        regulator_code=regulator_code,
        title="KYC Risk Master Direction",
        document_type="regulation",
    )
    session.add(regulation)
    session.flush()
    version = RegulationVersion(
        regulation_id=regulation.id,
        version=f"risk-{suffix}",
        content_hash=f"risk-hash-{suffix}",
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
        criticality=criticality,
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
    org = Organization(name=f"Risk Org {suffix}", slug=f"risk-org-{suffix}")
    session.add(org)
    session.flush()
    document = OrganizationDocument(
        organization_id=org.id,
        document_name="risk_company_policy.pdf",
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
def test_compliance_risk_scoring_end_to_end(db_session: Session) -> None:
    """Full end-to-end integration test: Step 2A -> Step 2B -> Step 3 Risk Scoring + DB persistence."""
    try:
        embedder = EmbeddingService()
        reg = _seed_regulation(db_session, embedder, IDENTITY_CLAUSE, criticality="HIGH")
    except Exception as exc:
        pytest.skip(f"Database unavailable or pgvector not configured: {exc}")

    org, doc = _seed_org_with_chunks(
        db_session,
        embedder,
        [(POLICY_IDENTITY, "Customer Identification", "1.1")],
    )

    try:
        matching_service = RegulatoryPolicyMatchingService(db_session, embedding_service=embedder)

        def mock_llm_handler(system_prompt: str, user_prompt: str, response_schema):
            chunk = (
                db_session.query(OrganizationPolicyChunk)
                .filter_by(organization_id=org.id, section_title="Customer Identification")
                .one()
            )
            return ComplianceAnalysisResult(
                compliance_status="COMPLIANT",
                confidence=0.90,
                reasoning="The policy directly requires customer identity verification.",
                evidence=[
                    EvidenceReference(
                        chunk_id=chunk.id,
                        document_id=doc.id,
                        similarity=0.88,
                        relevance="supports",
                        explanation="Mandatory customer identity check.",
                    )
                ],
                gaps=[],
            )

        mock_llm = MockLLMClient(response_provider=mock_llm_handler)
        compliance_service = ComplianceAnalysisService(
            matching_service=matching_service,
            llm_client=mock_llm,
        )
        risk_service = ComplianceRiskScoringService(
            compliance_analysis_service=compliance_service,
            db_session=db_session,
        )

        response = risk_service.evaluate_risk(
            organization_id=org.id,
            regulatory_clause_id=reg["clause_id"],
            top_k=5,
            similarity_threshold=0.60,
        )

        # 1. Verify schema response properties
        assert response.id is not None
        assert response.organization_id == org.id
        assert response.regulatory_clause_id == reg["clause_id"]
        assert response.compliance_status == "COMPLIANT"
        assert response.risk_level in [RiskScoreLevel.LOW, RiskScoreLevel.MEDIUM]
        assert 0.0 <= response.risk_score <= 100.0
        assert response.confidence == 0.90
        assert "factor_breakdown" in response.model_dump()
        assert "explanation" in response.model_dump()

        # 2. Verify database persistence
        saved = (
            db_session.query(ComplianceRiskAssessment)
            .filter_by(id=response.id)
            .one_or_none()
        )
        assert saved is not None
        assert saved.organization_id == org.id
        assert saved.regulatory_clause_id == reg["clause_id"]
        assert saved.compliance_status == "COMPLIANT"
        assert saved.risk_score == response.risk_score
        assert saved.risk_level == response.risk_level.value
        assert saved.confidence == response.confidence
        assert saved.factor_breakdown is not None
        assert "compliance_severity" in saved.factor_breakdown
        assert "regulatory_criticality" in saved.factor_breakdown
        assert saved.explanation == response.explanation

    finally:
        _cleanup(
            db_session,
            org_ids=[org.id],
            version_id=reg["version_id"],
            regulation_id=reg["regulation_id"],
            regulator_code=reg["regulator_code"],
        )


@pytest.mark.integration
def test_compliance_risk_scoring_organization_isolation(db_session: Session) -> None:
    """Ensure multi-tenant isolation: Org A policies are never used for Org B risk assessment."""
    try:
        embedder = EmbeddingService()
        reg = _seed_regulation(db_session, embedder, IDENTITY_CLAUSE, criticality="CRITICAL")
    except Exception as exc:
        pytest.skip(f"Database unavailable or pgvector not configured: {exc}")

    org_a, doc_a = _seed_org_with_chunks(
        db_session,
        embedder,
        [(POLICY_IDENTITY, "Customer Identification", "1.1")],
    )
    org_b, doc_b = _seed_org_with_chunks(
        db_session,
        embedder,
        [(POLICY_STATIONERY, "Office Supplies", "9.1")],
    )

    try:
        matching_service = RegulatoryPolicyMatchingService(db_session, embedding_service=embedder)

        def mock_llm_handler(system_prompt: str, user_prompt: str, response_schema):
            chunk = (
                db_session.query(OrganizationPolicyChunk)
                .filter_by(organization_id=org_a.id, section_title="Customer Identification")
                .one()
            )
            return ComplianceAnalysisResult(
                compliance_status="COMPLIANT",
                confidence=0.95,
                reasoning="Identity verified.",
                evidence=[
                    EvidenceReference(
                        chunk_id=chunk.id,
                        document_id=doc_a.id,
                        similarity=0.92,
                        relevance="supports",
                        explanation="Identity policy matches.",
                    )
                ],
                gaps=[],
            )

        mock_llm = MockLLMClient(response_provider=mock_llm_handler)
        compliance_service = ComplianceAnalysisService(
            matching_service=matching_service,
            llm_client=mock_llm,
        )
        risk_service = ComplianceRiskScoringService(
            compliance_analysis_service=compliance_service,
            db_session=db_session,
        )

        response_a = risk_service.evaluate_risk(
            organization_id=org_a.id,
            regulatory_clause_id=reg["clause_id"],
        )
        assert response_a.compliance_status == "COMPLIANT"

        # Org B has stationery policy, does NOT match identity clause
        response_b = risk_service.evaluate_risk(
            organization_id=org_b.id,
            regulatory_clause_id=reg["clause_id"],
        )
        assert response_b.compliance_status == "INSUFFICIENT_EVIDENCE"
        assert response_b.risk_score > response_a.risk_score

        # Check DB records isolation
        records_a = (
            db_session.query(ComplianceRiskAssessment)
            .filter_by(organization_id=org_a.id)
            .all()
        )
        records_b = (
            db_session.query(ComplianceRiskAssessment)
            .filter_by(organization_id=org_b.id)
            .all()
        )
        assert len(records_a) == 1
        assert len(records_b) == 1
        assert records_a[0].id != records_b[0].id
        assert records_a[0].compliance_status == "COMPLIANT"
        assert records_b[0].compliance_status == "INSUFFICIENT_EVIDENCE"

    finally:
        _cleanup(
            db_session,
            org_ids=[org_a.id, org_b.id],
            version_id=reg["version_id"],
            regulation_id=reg["regulation_id"],
            regulator_code=reg["regulator_code"],
        )
