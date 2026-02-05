"""
Tests for the health check endpoint.
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestHealthEndpoint:
    """Test cases for the health check endpoint."""

    def test_health_returns_ok(self, api_client):
        """Health endpoint returns 200 with status ok."""
        response = api_client.get("/health/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "ok"

    def test_health_is_publicly_accessible(self, api_client):
        """Health endpoint does not require authentication."""
        # api_client is not authenticated by default
        response = api_client.get("/health/")
        assert response.status_code == status.HTTP_200_OK
