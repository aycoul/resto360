"""Tests for driver models and API."""

import pytest
from django.utils import timezone
from rest_framework import status

from apps.authentication.tests.factories import UserFactory
from apps.delivery.models import Driver

from .factories import DriverFactory


@pytest.mark.django_db
class TestDriverModel:
    """Tests for Driver model."""

    def test_create_driver(self, restaurant):
        """Test creating a driver."""
        user = UserFactory(restaurant=restaurant, role="driver")

        driver = Driver.objects.create(
            restaurant=restaurant,
            user=user,
            phone=user.phone,
            vehicle_type="motorcycle",
        )

        assert driver.id is not None
        assert driver.is_available is False
        assert driver.current_location is None

    def test_go_online(self, restaurant):
        """Test driver going online."""
        driver = DriverFactory(restaurant=restaurant)

        driver.go_online()

        assert driver.is_available is True
        assert driver.went_online_at is not None

    def test_go_offline(self, restaurant):
        """Test driver going offline."""
        driver = DriverFactory(restaurant=restaurant, is_available=True)
        driver.went_online_at = timezone.now()
        driver.save()

        driver.go_offline()

        assert driver.is_available is False
        assert driver.went_online_at is None

    def test_update_location(self, restaurant):
        """Test updating driver location."""
        driver = DriverFactory(restaurant=restaurant)

        driver.update_location(lat=5.33, lng=-4.01)

        assert driver.current_location is not None
        assert driver.current_location.y == 5.33  # GIS: y=lat
        assert driver.current_location.x == -4.01  # GIS: x=lng
        assert driver.location_updated_at is not None


@pytest.mark.django_db
class TestDriverAPI:
    """Tests for driver API endpoints."""

    def test_list_drivers(self, auth_client, restaurant):
        """Test listing drivers."""
        DriverFactory(restaurant=restaurant)
        DriverFactory(restaurant=restaurant)

        response = auth_client.get("/api/v1/delivery/drivers/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_list_drivers_tenant_isolation(self, auth_client, restaurant):
        """Test drivers are filtered by restaurant."""
        DriverFactory(restaurant=restaurant)
        DriverFactory()  # Different restaurant

        response = auth_client.get("/api/v1/delivery/drivers/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_driver(self, auth_client, restaurant):
        """Test creating a driver profile."""
        user = UserFactory(restaurant=restaurant, role="driver")

        data = {
            "user": str(user.id),
            "phone": "+225 07 00 00 00",
            "vehicle_type": "motorcycle",
            "vehicle_plate": "AB-1234-CI",
        }

        response = auth_client.post(
            "/api/v1/delivery/drivers/", data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"] == str(user.id)
        assert response.data["vehicle_type"] == "motorcycle"

    def test_create_driver_wrong_role(self, auth_client, restaurant):
        """Test creating driver for non-driver user fails."""
        user = UserFactory(restaurant=restaurant, role="cashier")

        data = {
            "user": str(user.id),
            "phone": user.phone,
            "vehicle_type": "motorcycle",
        }

        response = auth_client.post(
            "/api/v1/delivery/drivers/", data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "driver" in str(response.data).lower()

    def test_toggle_availability_online(self, auth_client, restaurant):
        """Test toggling driver to online."""
        driver = DriverFactory(restaurant=restaurant, is_available=False)

        response = auth_client.post(
            f"/api/v1/delivery/drivers/{driver.id}/toggle_availability/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_available"] is True
        assert response.data["went_online_at"] is not None

    def test_toggle_availability_offline(self, auth_client, restaurant):
        """Test toggling driver to offline."""
        driver = DriverFactory(restaurant=restaurant, is_available=True)

        response = auth_client.post(
            f"/api/v1/delivery/drivers/{driver.id}/toggle_availability/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_available"] is False

    def test_update_location(self, auth_client, restaurant):
        """Test updating driver location."""
        driver = DriverFactory(restaurant=restaurant)

        response = auth_client.post(
            f"/api/v1/delivery/drivers/{driver.id}/update_location/",
            {"lat": 5.33, "lng": -4.01},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["latitude"] == 5.33
        assert response.data["longitude"] == -4.01
        assert response.data["location_updated_at"] is not None

    def test_update_location_validation(self, auth_client, restaurant):
        """Test location update validates coordinates."""
        driver = DriverFactory(restaurant=restaurant)

        response = auth_client.post(
            f"/api/v1/delivery/drivers/{driver.id}/update_location/",
            {"lat": 100, "lng": -4.01},  # Invalid latitude
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_current_driver_profile(self, auth_client, restaurant, user):
        """Test getting current user's driver profile."""
        # Create driver profile for authenticated user
        user.role = "driver"
        user.save()
        driver = Driver.objects.create(
            restaurant=restaurant,
            user=user,
            phone=user.phone,
        )

        response = auth_client.get("/api/v1/delivery/drivers/me/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(driver.id)

    def test_get_current_driver_profile_not_found(self, auth_client, restaurant):
        """Test getting driver profile when none exists."""
        response = auth_client.get("/api/v1/delivery/drivers/me/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
