from datetime import datetime
from uuid import uuid4
from types import SimpleNamespace

from app.models.clause import Clause
from app.models.organization import Organization
from app.models.organization_document import OrganizationDocument
from app.models.organization_policy_chunk import OrganizationPolicyChunk
from app.services.document_compliance_service import DocumentComplianceService


def _build_document_service():
    return DocumentComplianceService(session=SimpleNamespace(), settings=None)


def test_get_policy_clauses_returns_document_chunks_in_order():
    service = _build_document_service()
    organization_id = uuid4()
    document_id = uuid4()
    policy_document = OrganizationDocument(
        id=document_id,
        organization_id=organization_id,
        document_name="policy.pdf",
        status="processed",
    )
    chunk1 = OrganizationPolicyChunk(
        id=uuid4(),
        document_id=document_id,
        organization_id=organization_id,
        chunk_index=2,
        section_title="KYC",
        clause_reference="2.1",
        content="Customer identity is verified before onboarding.",
        embedding=[0.1] * 1024,
    )
    chunk2 = OrganizationPolicyChunk(
        id=uuid4(),
        document_id=document_id,
        organization_id=organization_id,
        chunk_index=1,
        section_title="AML",
        clause_reference="1.1",
        content="The bank verifies customer identity before account opening.",
        embedding=[0.2] * 1024,
    )

    clauses = service._sort_policy_clauses([chunk1, chunk2])
    assert [row.chunk_index for row in clauses] == [1, 2]
    assert clauses[0].content.startswith("The bank")
    assert clauses[1].section_title == "KYC"


def test_analyze_document_generates_summary_from_relevant_matches():
    service = _build_document_service()
    organization_id = uuid4()
    document_id = uuid4()
    policy_document = OrganizationDocument(
        id=document_id,
        organization_id=organization_id,
        document_name="policy.pdf",
        status="processed",
    )
    policy_clause = OrganizationPolicyChunk(
        id=uuid4(),
        document_id=document_id,
        organization_id=organization_id,
        chunk_index=1,
        section_title="Customer ID",
        clause_reference="1.1",
        content="Customer identity is verified prior to account opening.",
        embedding=[0.1] * 1024,
    )

    service.get_policy_clauses = lambda *args, **kwargs: [policy_clause]
    service._match_policy_clause = lambda *args, **kwargs: [
        SimpleNamespace(
            regulatory_clause_id=uuid4(),
            matching_score=0.91,
            compliance_score=88.0,
            status="COMPLIANT",
            explanation="The policy explicitly requires identity verification before onboarding.",
            policy_evidence="Customer identity is verified prior to account opening.",
            regulatory_requirement="Verify customer identity before account opening.",
            recommendation=None,
        )
    ]

    report = service.analyze_document(organization_id=organization_id, policy_document_id=document_id)

    assert report["overall_score"] >= 80
    assert report["summary"]["compliant_count"] == 1
    assert report["results"][0]["status"] == "COMPLIANT"
    assert report["results"][0]["matching_score"] == 0.91
    assert report["results"][0]["compliance_score"] == 88.0


def test_match_policy_clause_uses_existing_regulatory_clause_ids():
    real_clause = Clause(
        id=uuid4(),
        version_id=uuid4(),
        clause_number="1.1",
        section="Customer Identification",
        title="Customer Identity Verification",
        text="Verify customer identity before account opening.",
        page_number=3,
        metadata_={},
    )

    class FakeScalarResult:
        def all(self):
            return [real_clause]

    service = DocumentComplianceService(session=SimpleNamespace(scalars=lambda stmt: FakeScalarResult()))
    policy_chunk = OrganizationPolicyChunk(
        id=uuid4(),
        document_id=uuid4(),
        organization_id=uuid4(),
        chunk_index=1,
        section_title="Customer ID",
        clause_reference="1.1",
        content="Customer identity is verified before onboarding.",
        embedding=[0.1] * 1024,
    )

    matches = service._match_policy_clause(
        organization_id=uuid4(),
        policy_clause=policy_chunk,
        top_k=5,
        similarity_threshold=0.6,
    )

    assert matches
    assert matches[0]["regulatory_clause_id"] == real_clause.id
    assert matches[0]["regulatory_requirement"] == real_clause.text
