"""API tests for organization policy upload and search."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.api.dependencies.services import get_organization_policy_service
from app.api.schemas.organization_document import (
    OrganizationDocumentIngestResponse,
    OrganizationPolicySearchHit,
    OrganizationPolicySearchResponse,
    OrganizationResponse,
)
from app.core.exceptions import NotFoundError, ValidationError


def test_create_organization_endpoint(client) -> None:
    org_id = uuid4()
    mock_service = MagicMock()
    mock_service.create_organization.return_value = OrganizationResponse(
        id=org_id,
        name="Acme Bank",
        slug="acme-bank",
    )
    client.app.dependency_overrides[get_organization_policy_service] = lambda: mock_service
    try:
        response = client.post(
            "/api/v1/organizations",
            json={"name": "Acme Bank", "slug": "acme-bank"},
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["id"] == str(org_id)


def test_upload_endpoint_accepts_pdf(client) -> None:
    org_id = uuid4()
    document_id = uuid4()
    mock_service = MagicMock()
    mock_service.upload_document.return_value = OrganizationDocumentIngestResponse(
        document_id=document_id,
        organization_id=org_id,
        document_name="company_kyc_policy.pdf",
        status="processed",
        chunks_created=42,
    )
    client.app.dependency_overrides[get_organization_policy_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/documents",
            files={"file": ("company_kyc_policy.pdf", b"%PDF-1.4 test", "application/pdf")},
            data={"document_type": "KYC_POLICY", "version": "2026.1"},
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "processed"
    assert payload["chunks_created"] == 42


def test_upload_endpoint_rejects_invalid_file(client) -> None:
    mock_service = MagicMock()
    mock_service.upload_document.side_effect = ValidationError(
        "Unsupported file type. Only PDF uploads are accepted."
    )
    client.app.dependency_overrides[get_organization_policy_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{uuid4()}/documents",
            files={"file": ("notes.txt", b"hello", "text/plain")},
            data={"document_type": "KYC_POLICY"},
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 422


def test_upload_endpoint_unknown_organization(client) -> None:
    org_id = uuid4()
    mock_service = MagicMock()
    mock_service.upload_document.side_effect = NotFoundError("Organization", str(org_id))
    client.app.dependency_overrides[get_organization_policy_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/documents",
            files={"file": ("policy.pdf", b"%PDF-1.4", "application/pdf")},
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 404


def test_search_endpoint_returns_results(client) -> None:
    org_id = uuid4()
    mock_service = MagicMock()
    mock_service.search.return_value = OrganizationPolicySearchResponse(
        query="What customer identification procedures are required?",
        organization_id=org_id,
        total_results=1,
        results=[
            OrganizationPolicySearchHit(
                chunk_id=uuid4(),
                document_id=uuid4(),
                document_name="company_kyc_policy.pdf",
                content="The organization shall verify customer identity.",
                section_title="Customer Identification",
                clause_reference="4.2",
                similarity=0.87,
            )
        ],
    )
    client.app.dependency_overrides[get_organization_policy_service] = lambda: mock_service
    try:
        response = client.post(
            f"/api/v1/organizations/{org_id}/documents/search",
            json={"query": "What customer identification procedures are required?", "top_k": 5},
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_results"] == 1
    assert payload["results"][0]["clause_reference"] == "4.2"


def test_search_endpoint_rejects_empty_query(client) -> None:
    response = client.post(
        f"/api/v1/organizations/{uuid4()}/documents/search",
        json={"query": "   "},
    )
    assert response.status_code == 422
