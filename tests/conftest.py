"""Pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

pytest_plugins = ["tests.integration.conftest"]

from main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)
