"""Driver assignment algorithm using PostGIS spatial queries."""

from datetime import timedelta
from typing import Optional

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db import transaction
from django.utils import timezone

from apps.delivery.models import Delivery, DeliveryStatus, DeliveryZone, Driver
from apps.orders.models import Order


def find_nearest_available_driver(
    restaurant,
    pickup_location: Point,
    max_distance_km: float = 10.0,
    max_stale_minutes: int = 5,
) -> Optional[Driver]:
    """
    Find the nearest available driver within range.

    Uses PostGIS ST_DWithin for efficient spatial index usage,
    then orders by distance using the Distance function.

    Args:
        restaurant: The restaurant (for tenant filtering)
        pickup_location: Point where driver needs to pick up order
        max_distance_km: Maximum distance in kilometers (default 10km)
        max_stale_minutes: Reject drivers with location older than this (default 5min)

    Returns:
        The nearest available Driver, or None if none available
    """
    # Only consider drivers with recent location updates
    stale_threshold = timezone.now() - timedelta(minutes=max_stale_minutes)

    # Convert km to meters (PostGIS geography uses meters)
    max_distance_meters = max_distance_km * 1000

    # Find available drivers ordered by distance
    # Using ST_DWithin first for index usage, then ordering by actual distance
    drivers = (
        Driver.objects.filter(
            restaurant=restaurant,
            is_available=True,
            current_location__isnull=False,
            location_updated_at__gte=stale_threshold,
        )
        .filter(
            # ST_DWithin for efficient spatial index filtering
            current_location__dwithin=(pickup_location, max_distance_meters)
        )
        .annotate(distance=Distance("current_location", pickup_location))
        .order_by("distance")
    )

    # Return first (nearest) driver, or None
    return drivers.first()


@transaction.atomic
def assign_driver_to_delivery(
    delivery_id, max_distance_km: float = 10.0
) -> Optional[Delivery]:
    """
    Assign the nearest available driver to a delivery.

    Uses select_for_update to prevent race conditions when
    multiple deliveries are assigned simultaneously.

    Args:
        delivery_id: UUID of the delivery to assign
        max_distance_km: Maximum distance for driver search

    Returns:
        The updated Delivery with driver assigned, or None if no driver available
    """
    # Lock the delivery row to prevent concurrent assignment attempts
    delivery = Delivery.all_objects.select_for_update().get(id=delivery_id)

    if delivery.driver is not None:
        return delivery  # Already assigned

    if delivery.status != DeliveryStatus.PENDING_ASSIGNMENT:
        return None  # Wrong status for assignment

    # Get pickup location from delivery (restaurant location)
    if not delivery.pickup_location:
        return None  # No pickup location set

    pickup_location = delivery.pickup_location

    driver = find_nearest_available_driver(
        restaurant=delivery.restaurant,
        pickup_location=pickup_location,
        max_distance_km=max_distance_km,
    )

    if driver is None:
        return None  # No driver available

    # Lock the driver row to prevent double-assignment
    driver = Driver.all_objects.select_for_update().get(id=driver.id)

    # Double-check driver is still available (may have been assigned while we were checking)
    if not driver.is_available:
        return None

    # Perform assignment using FSM transition
    delivery.assign(driver)
    delivery.save()

    # Mark driver as busy (not available for other deliveries)
    driver.is_available = False
    driver.save(update_fields=["is_available"])

    return delivery


def create_delivery_for_order(
    order: Order,
    delivery_address: str,
    delivery_lat: float,
    delivery_lng: float,
    delivery_notes: str = "",
) -> Delivery:
    """
    Create a Delivery record for an order.

    Args:
        order: The Order to create delivery for
        delivery_address: Customer's delivery address
        delivery_lat: Delivery latitude
        delivery_lng: Delivery longitude
        delivery_notes: Optional delivery instructions

    Returns:
        Created Delivery object

    Raises:
        ValueError: If delivery address is outside all delivery zones
    """
    restaurant = order.restaurant
    delivery_point = Point(delivery_lng, delivery_lat, srid=4326)  # GIS: lng, lat

    # Find zone for delivery address
    zone = DeliveryZone.find_zone_for_location(
        restaurant=restaurant, lat=delivery_lat, lng=delivery_lng
    )

    if not zone:
        raise ValueError("Delivery address is outside all delivery zones")

    # Get restaurant location for pickup
    pickup_location = None
    if restaurant.latitude and restaurant.longitude:
        pickup_location = Point(
            float(restaurant.longitude), float(restaurant.latitude), srid=4326
        )

    # Calculate estimated delivery time
    estimated_minutes = zone.estimated_time_minutes
    estimated_delivery = timezone.now() + timedelta(minutes=estimated_minutes)

    delivery = Delivery.objects.create(
        restaurant=restaurant,
        order=order,
        zone=zone,
        pickup_address=restaurant.address or "",
        pickup_location=pickup_location,
        delivery_address=delivery_address,
        delivery_location=delivery_point,
        delivery_notes=delivery_notes,
        delivery_fee=zone.delivery_fee,
        estimated_delivery_time=estimated_delivery,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
    )

    return delivery
