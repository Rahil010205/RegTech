"""API tests for GET /api/v1/organizations (list + pagination)."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.api.dependencies.services import get_organization_policy_service
from app.api.schemas.organization import PaginatedOrganizationResponse
from app.api.schemas.organization_document import OrganizationResponse


def test_list_organizations_returns_paginated(client) -> None:
    """GET /organizations returns items, total, skip, limit."""
    org_id = uuid4()
    mock_service = MagicMock()
    mock_service.list_organizations.return_value = PaginatedOrganizationResponse(
        items=[OrganizationResponse(id=org_id, name="Acme Bank", slug="acme-bank")],
        total=1,
        skip=0,
        limit=20,
    )
    client.app.dependency_overrides[get_organization_policy_service] = lambda: mock_service
    try:
        response = client.get("/api/v1/organizations/")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["skip"] == 0
    assert payload["limit"] == 20
    assert len(payload["items"]) == 1
    assert payload["items"][0]["slug"] == "acme-bank"


def test_list_organizations_with_pagination_params(client) -> None:
    """GET /organizations?skip=10&limit=5 passes params through."""
    mock_service = MagicMock()
    mock_service.list_organizations.return_value = PaginatedOrganizationResponse(
        items=[],
        total=100,
        skip=10,
        limit=5,
    )
    client.app.dependency_overrides[get_organization_policy_service] = lambda: mock_service
    try:
        response = client.get("/api/v1/organizations/", params={"skip": 10, "limit": 5})
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["skip"] == 10
    assert payload["limit"] == 5
    assert payload["total"] == 100
    mock_service.list_organizations.assert_called_once_with(skip=10, limit=5)


def test_list_organizations_invalid_skip_rejected(client) -> None:
    """skip < 0 must be rejected with 422."""
    response = client.get("/api/v1/organizations/", params={"skip": -1})
    assert response.status_code == 422


def test_list_organizations_invalid_limit_rejected(client) -> None:
    """limit = 0 must be rejected with 422; limit > 100 must also be rejected."""
    response = client.get("/api/v1/organizations/", params={"limit": 0})
    assert response.status_code == 422

    response = client.get("/api/v1/organizations/", params={"limit": 101})
    assert response.status_code == 422


def test_list_organizations_empty(client) -> None:
    """Returns an empty items list with total=0 when no orgs exist."""
    mock_service = MagicMock()
    mock_service.list_organizations.return_value = PaginatedOrganizationResponse(
        items=[],
        total=0,
        skip=0,
        limit=20,
    )
    client.app.dependency_overrides[get_organization_policy_service] = lambda: mock_service
    try:
        response = client.get("/api/v1/organizations/")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 0
    assert payload["items"] == []
