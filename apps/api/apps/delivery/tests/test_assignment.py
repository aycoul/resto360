"""Tests for driver assignment service."""

from datetime import timedelta

import pytest
from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.delivery.models import DeliveryStatus
from apps.delivery.services import (
    assign_driver_to_delivery,
    create_delivery_for_order,
    find_nearest_available_driver,
)

from .factories import DeliveryFactory, DeliveryZoneFactory, DriverFactory


@pytest.mark.django_db
class TestFindNearestDriver:
    """Tests for find_nearest_available_driver."""

    def test_finds_nearest_driver(self, business):
        """Test finding the nearest available driver."""
        # Create two drivers at different distances
        driver_near = DriverFactory(business=business, is_available=True)
        driver_near.update_location(lat=5.33, lng=-4.01)  # Very close

        driver_far = DriverFactory(business=business, is_available=True)
        driver_far.update_location(lat=5.35, lng=-4.03)  # Further away

        pickup = Point(-4.01, 5.33, srid=4326)

        result = find_nearest_available_driver(
            business=business, pickup_location=pickup
        )

        assert result == driver_near

    def test_excludes_unavailable_drivers(self, business):
        """Test that unavailable drivers are excluded."""
        driver = DriverFactory(business=business, is_available=False)
        driver.update_location(lat=5.33, lng=-4.01)

        pickup = Point(-4.01, 5.33, srid=4326)

        result = find_nearest_available_driver(
            business=business, pickup_location=pickup
        )

        assert result is None

    def test_excludes_stale_locations(self, business):
        """Test that drivers with stale locations are excluded."""
        driver = DriverFactory(business=business, is_available=True)
        driver.current_location = Point(-4.01, 5.33, srid=4326)
        driver.location_updated_at = timezone.now() - timedelta(minutes=10)  # Stale
        driver.save()

        pickup = Point(-4.01, 5.33, srid=4326)

        result = find_nearest_available_driver(
            business=business, pickup_location=pickup, max_stale_minutes=5
        )

        assert result is None

    def test_excludes_drivers_outside_range(self, business):
        """Test that drivers outside max distance are excluded."""
        driver = DriverFactory(business=business, is_available=True)
        driver.update_location(lat=6.0, lng=-3.0)  # Far away

        pickup = Point(-4.01, 5.33, srid=4326)

        result = find_nearest_available_driver(
            business=business,
            pickup_location=pickup,
            max_distance_km=5,  # 5km max
        )

        assert result is None

    def test_excludes_drivers_without_location(self, business):
        """Test that drivers without location are excluded."""
        driver = DriverFactory(business=business, is_available=True)
        # No location set

        pickup = Point(-4.01, 5.33, srid=4326)

        result = find_nearest_available_driver(
            business=business, pickup_location=pickup
        )

        assert result is None


@pytest.mark.django_db
class TestAssignDriverToDelivery:
    """Tests for assign_driver_to_delivery."""

    def test_assigns_nearest_driver(self, business):
        """Test assigning nearest driver to delivery."""
        # Setup driver
        driver = DriverFactory(business=business, is_available=True)
        driver.update_location(lat=5.33, lng=-4.01)

        # Setup delivery
        delivery = DeliveryFactory(business=business)

        result = assign_driver_to_delivery(delivery.id)

        assert result is not None
        assert result.driver == driver
        assert result.status == DeliveryStatus.ASSIGNED

        # Driver should now be unavailable
        driver.refresh_from_db()
        assert driver.is_available is False

    def test_no_assignment_if_no_drivers(self, business):
        """Test no assignment when no drivers available."""
        delivery = DeliveryFactory(business=business)

        result = assign_driver_to_delivery(delivery.id)

        assert result is None
        delivery.refresh_from_db()
        assert delivery.status == DeliveryStatus.PENDING_ASSIGNMENT

    def test_no_double_assignment(self, business):
        """Test delivery can't be assigned twice."""
        driver1 = DriverFactory(business=business, is_available=True)
        driver1.update_location(lat=5.33, lng=-4.01)

        driver2 = DriverFactory(business=business, is_available=True)
        driver2.update_location(lat=5.33, lng=-4.01)

        delivery = DeliveryFactory(business=business)

        # First assignment
        result1 = assign_driver_to_delivery(delivery.id)
        assert result1.driver is not None

        # Second assignment attempt
        result2 = assign_driver_to_delivery(delivery.id)
        assert result2.driver == result1.driver  # Same driver

    def test_no_assignment_if_already_assigned(self, business):
        """Test no assignment for already-assigned delivery."""
        driver = DriverFactory(business=business, is_available=True)
        driver.update_location(lat=5.33, lng=-4.01)

        delivery = DeliveryFactory(business=business)
        delivery.assign(driver)
        delivery.save()

        # Try to assign again
        result = assign_driver_to_delivery(delivery.id)

        # Should return the same delivery with same driver
        assert result.driver == driver

    def test_no_assignment_wrong_status(self, business):
        """Test no assignment for delivery not in pending_assignment status."""
        driver = DriverFactory(business=business, is_available=True)
        delivery = DeliveryFactory(business=business)

        # Manually set wrong status by manipulating the FSM
        delivery.assign(driver)
        delivery.save()
        delivery.mark_picked_up()
        delivery.save()

        driver2 = DriverFactory(business=business, is_available=True)
        driver2.update_location(lat=5.33, lng=-4.01)

        # Try to assign
        result = assign_driver_to_delivery(delivery.id)

        assert result is None  # Can't assign to picked_up delivery


@pytest.mark.django_db
class TestCreateDeliveryForOrder:
    """Tests for create_delivery_for_order."""

    def test_creates_delivery(self, business, order):
        """Test creating delivery for order."""
        business.latitude = 5.33
        business.longitude = -4.01
        business.save()

        DeliveryZoneFactory(business=business)

        delivery = create_delivery_for_order(
            order=order,
            delivery_address="123 Customer St",
            delivery_lat=5.33,
            delivery_lng=-4.01,
            delivery_notes="Ring doorbell",
        )

        assert delivery.id is not None
        assert delivery.order == order
        assert delivery.delivery_address == "123 Customer St"
        assert delivery.delivery_notes == "Ring doorbell"
        assert delivery.delivery_fee > 0
        assert delivery.estimated_delivery_time is not None

    def test_fails_outside_zones(self, business, order):
        """Test creating delivery fails if outside all zones."""
        DeliveryZoneFactory(business=business)

        with pytest.raises(ValueError, match="outside"):
            create_delivery_for_order(
                order=order,
                delivery_address="Far Away",
                delivery_lat=10.0,  # Outside zone
                delivery_lng=10.0,
            )

    def test_copies_customer_info(self, business, order):
        """Test that customer info is copied from order."""
        business.latitude = 5.33
        business.longitude = -4.01
        business.address = "Business Address"
        business.save()

        order.customer_name = "Test Customer"
        order.customer_phone = "+2250700000000"
        order.save()

        DeliveryZoneFactory(business=business)

        delivery = create_delivery_for_order(
            order=order,
            delivery_address="123 Customer St",
            delivery_lat=5.33,
            delivery_lng=-4.01,
        )

        assert delivery.customer_name == "Test Customer"
        assert delivery.customer_phone == "+2250700000000"
        assert delivery.pickup_address == "Restaurant Address"
