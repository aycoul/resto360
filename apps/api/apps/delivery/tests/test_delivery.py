"""Tests for Delivery model and API."""

import pytest
from django.contrib.gis.geos import Point, Polygon
from rest_framework import status

from apps.delivery.models import Delivery, DeliveryStatus, DeliveryZone

from .factories import DeliveryFactory, DeliveryZoneFactory, DriverFactory


@pytest.mark.django_db
class TestDeliveryModel:
    """Tests for Delivery model."""

    def test_create_delivery(self, business, order):
        """Test creating a delivery."""
        zone = DeliveryZone.objects.create(
            business=business,
            name="Test Zone",
            polygon=Polygon(
                [
                    (-4.02, 5.32),
                    (-4.02, 5.34),
                    (-4.00, 5.34),
                    (-4.00, 5.32),
                    (-4.02, 5.32),
                ],
                srid=4326,
            ),
            delivery_fee=1500,
        )

        delivery = Delivery.objects.create(
            business=business,
            order=order,
            zone=zone,
            pickup_address="Restaurant",
            delivery_address="Customer",
            delivery_location=Point(-4.01, 5.33, srid=4326),
            delivery_fee=1500,
        )

        assert delivery.status == DeliveryStatus.PENDING_ASSIGNMENT
        assert delivery.driver is None

    def test_fsm_assign(self, business):
        """Test assigning driver via FSM transition."""
        delivery = DeliveryFactory(business=business)
        driver = DriverFactory(business=business, is_available=True)

        delivery.assign(driver)
        delivery.save()

        assert delivery.status == DeliveryStatus.ASSIGNED
        assert delivery.driver == driver
        assert delivery.assigned_at is not None

    def test_fsm_full_flow(self, business):
        """Test full delivery status flow."""
        delivery = DeliveryFactory(business=business)
        driver = DriverFactory(business=business)

        # Assign
        delivery.assign(driver)
        delivery.save()
        assert delivery.status == DeliveryStatus.ASSIGNED

        # Pick up
        delivery.mark_picked_up()
        delivery.save()
        assert delivery.status == DeliveryStatus.PICKED_UP

        # En route
        delivery.mark_en_route()
        delivery.save()
        assert delivery.status == DeliveryStatus.EN_ROUTE

        # Deliver
        delivery.mark_delivered(
            proof_type="signature", proof_data="base64...", recipient_name="John"
        )
        delivery.save()
        assert delivery.status == DeliveryStatus.DELIVERED
        assert delivery.proof_type == "signature"

    def test_fsm_cancel(self, business):
        """Test cancelling delivery."""
        delivery = DeliveryFactory(business=business)

        delivery.cancel(reason="Customer not available")
        delivery.save()

        assert delivery.status == DeliveryStatus.CANCELLED
        assert delivery.cancelled_reason == "Customer not available"


@pytest.mark.django_db
class TestDeliveryAPI:
    """Tests for delivery API endpoints."""

    def test_list_deliveries(self, auth_client, business):
        """Test listing deliveries."""
        DeliveryFactory(business=business)
        DeliveryFactory(business=business)

        response = auth_client.get("/api/v1/delivery/deliveries/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_retrieve_delivery(self, auth_client, business):
        """Test retrieving a single delivery."""
        delivery = DeliveryFactory(business=business)

        response = auth_client.get(f"/api/v1/delivery/deliveries/{delivery.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(delivery.id)

    def test_update_status_picked_up(self, auth_client, business):
        """Test updating delivery status to picked_up."""
        delivery = DeliveryFactory(business=business)
        driver = DriverFactory(business=business)
        delivery.assign(driver)
        delivery.save()

        response = auth_client.post(
            f"/api/v1/delivery/deliveries/{delivery.id}/update_status/",
            {"status": "picked_up"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == DeliveryStatus.PICKED_UP

    def test_confirm_delivery(self, auth_client, business):
        """Test confirming delivery with signature."""
        delivery = DeliveryFactory(business=business)
        driver = DriverFactory(business=business)
        delivery.assign(driver)
        delivery.save()
        delivery.mark_picked_up()
        delivery.save()
        delivery.mark_en_route()
        delivery.save()

        response = auth_client.post(
            f"/api/v1/delivery/deliveries/{delivery.id}/confirm/",
            {
                "proof_type": "signature",
                "proof_data": "base64signaturedata",
                "recipient_name": "John Doe",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == DeliveryStatus.DELIVERED
        assert response.data["proof_type"] == "signature"

    def test_assign_delivery(self, auth_client, business):
        """Test manual assignment endpoint."""
        delivery = DeliveryFactory(business=business)
        driver = DriverFactory(business=business, is_available=True)
        driver.update_location(lat=5.33, lng=-4.01)

        response = auth_client.post(
            f"/api/v1/delivery/deliveries/{delivery.id}/assign/",
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == DeliveryStatus.ASSIGNED
        assert response.data["driver"] == str(driver.id)

    def test_assign_delivery_no_drivers(self, auth_client, business):
        """Test assignment fails when no drivers available."""
        delivery = DeliveryFactory(business=business)

        response = auth_client.post(
            f"/api/v1/delivery/deliveries/{delivery.id}/assign/",
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No available drivers" in response.data["error"]

    def test_active_deliveries(self, auth_client, business, user):
        """Test getting active deliveries for driver."""
        driver = DriverFactory(business=business, user=user)
        delivery = DeliveryFactory(business=business)
        delivery.assign(driver)
        delivery.save()

        response = auth_client.get("/api/v1/delivery/deliveries/active/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(delivery.id)
