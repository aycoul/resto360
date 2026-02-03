"""
pytest configuration and fixtures for RESTO360 API tests.
"""
import pytest


@pytest.fixture(scope="session")
def django_db_setup():
    """Configure test database.

    Using in-memory SQLite as configured in testing settings.
    """
    pass


@pytest.fixture
def api_client():
    """Return a DRF test client for API testing."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def authenticated_client(api_client, django_user_model):
    """Return an authenticated API client."""
    user = django_user_model.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )
    api_client.force_authenticate(user=user)
    return api_client
