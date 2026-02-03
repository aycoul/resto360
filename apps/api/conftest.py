"""
pytest configuration and fixtures for RESTO360 API tests.
"""
import pytest


@pytest.fixture
def api_client():
    """Return a DRF test client for API testing."""
    from rest_framework.test import APIClient

    return APIClient()
