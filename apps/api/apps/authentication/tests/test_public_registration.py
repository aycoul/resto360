"""Tests for public registration endpoint (RESTO360 Lite)."""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import Business, User


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def registration_data():
    """Return valid registration data."""
    return {
        "email": "test@example.com",
        "password": "TestPass123!",
        "password_confirm": "TestPass123!",
        "business_name": "Test Restaurant",
        "phone": "+2250700000001",
    }


@pytest.mark.django_db
class TestPublicRegistration:
    """Test cases for public registration endpoint."""

    def test_public_registration_success(self, api_client, registration_data):
        """Test successful registration creates restaurant and user with JWT tokens."""
        response = api_client.post(
            "/api/auth/register/",
            registration_data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Verify response structure
        data = response.json()
        assert "restaurant" in data
        assert "user" in data
        assert "access" in data
        assert "refresh" in data

        # Verify restaurant data
        assert data["restaurant"]["name"] == registration_data["business_name"]
        assert "slug" in data["restaurant"]
        assert data["restaurant"]["id"]

        # Verify user data
        assert data["user"]["role"] == "owner"
        assert data["user"]["name"] == f"{registration_data['business_name']} Owner"
        assert data["user"]["id"]

        # Verify database records
        business = Business.objects.get(id=data["restaurant"]["id"])
        assert business.plan_type == "free"
        assert business.email == registration_data["email"]
        assert business.phone == registration_data["phone"]

        user = User.objects.get(id=data["user"]["id"])
        assert user.role == "owner"
        assert user.business == business
        assert user.email == registration_data["email"]
        assert user.phone == registration_data["phone"]

    def test_public_registration_password_mismatch(
        self, api_client, registration_data
    ):
        """Test registration fails when passwords don't match."""
        registration_data["password_confirm"] = "DifferentPass123!"

        response = api_client.post(
            "/api/auth/register/",
            registration_data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "password_confirm" in data
        assert "do not match" in data["password_confirm"][0].lower()

    def test_public_registration_duplicate_phone(
        self, api_client, registration_data
    ):
        """Test registration fails when phone number already exists."""
        # Create existing user with same phone
        business = Business.objects.create(
            name="Existing Business",
            slug="existing-business",
            phone=registration_data["phone"],
        )
        User.objects.create_user(
            phone=registration_data["phone"],
            password="password123",
            name="Existing User",
            business=business,
        )

        response = api_client.post(
            "/api/auth/register/",
            registration_data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "phone" in data
        assert "already exists" in data["phone"][0].lower()

    def test_public_registration_duplicate_email(
        self, api_client, registration_data
    ):
        """Test registration fails when email already exists."""
        # Create existing user with same email
        business = Business.objects.create(
            name="Existing Business",
            slug="existing-business",
            phone="+2250700000099",
        )
        User.objects.create_user(
            phone="+2250700000099",
            email=registration_data["email"],
            password="password123",
            name="Existing User",
            business=business,
        )

        response = api_client.post(
            "/api/auth/register/",
            registration_data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "email" in data
        assert "already exists" in data["email"][0].lower()

    def test_public_registration_creates_unique_slug(self, api_client):
        """Test that registering with same restaurant name creates unique slugs."""
        data1 = {
            "email": "test1@example.com",
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
            "business_name": "Test Restaurant",
            "phone": "+2250700000001",
        }
        data2 = {
            "email": "test2@example.com",
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
            "business_name": "Test Restaurant",
            "phone": "+2250700000002",
        }

        response1 = api_client.post("/api/auth/register/", data1, format="json")
        response2 = api_client.post("/api/auth/register/", data2, format="json")

        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_201_CREATED

        slug1 = response1.json()["restaurant"]["slug"]
        slug2 = response2.json()["restaurant"]["slug"]

        # Both should have unique slugs
        assert slug1 != slug2
        assert "test-restaurant" in slug1
        assert "test-restaurant" in slug2

    def test_public_registration_missing_required_fields(self, api_client):
        """Test registration fails with missing required fields."""
        # Missing email
        response = api_client.post(
            "/api/auth/register/",
            {
                "password": "TestPass123!",
                "password_confirm": "TestPass123!",
                "business_name": "Test Restaurant",
                "phone": "+2250700000001",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.json()

        # Missing password
        response = api_client.post(
            "/api/auth/register/",
            {
                "email": "test@example.com",
                "password_confirm": "TestPass123!",
                "business_name": "Test Restaurant",
                "phone": "+2250700000001",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.json()

    def test_public_registration_short_password(self, api_client, registration_data):
        """Test registration fails with password shorter than 8 characters."""
        registration_data["password"] = "short"
        registration_data["password_confirm"] = "short"

        response = api_client.post(
            "/api/auth/register/",
            registration_data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "password" in data
