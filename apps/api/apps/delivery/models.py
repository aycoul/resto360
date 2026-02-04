"""Delivery models for RESTO360."""

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.db import models
from django.utils import timezone

from apps.core.managers import TenantManager
from apps.core.models import TenantModel


class DeliveryZone(TenantModel):
    """
    Delivery zone with polygon boundary.

    Uses PostGIS geography type for automatic meter-based distance calculations.
    """

    name = models.CharField(max_length=100)
    # geography=True for lat/lng with distances in meters
    polygon = gis_models.PolygonField(geography=True, srid=4326)
    delivery_fee = models.PositiveIntegerField(help_text="Delivery fee in XOF")
    minimum_order = models.PositiveIntegerField(
        default=0, help_text="Minimum order amount in XOF"
    )
    estimated_time_minutes = models.PositiveIntegerField(
        default=30, help_text="Base estimated delivery time in minutes"
    )
    is_active = models.BooleanField(default=True)

    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"

    def contains_point(self, lat: float, lng: float) -> bool:
        """Check if a point is within this zone."""
        # GIS uses (lng, lat) order!
        point = Point(lng, lat, srid=4326)
        return self.polygon.contains(point)

    @classmethod
    def find_zone_for_location(cls, restaurant, lat: float, lng: float):
        """Find the delivery zone containing a location."""
        point = Point(lng, lat, srid=4326)
        return cls.objects.filter(
            restaurant=restaurant, polygon__contains=point, is_active=True
        ).first()


class VehicleType(models.TextChoices):
    """Driver vehicle type enumeration."""

    MOTORCYCLE = "motorcycle", "Motorcycle"
    BICYCLE = "bicycle", "Bicycle"
    CAR = "car", "Car"
    FOOT = "foot", "On Foot"


class Driver(TenantModel):
    """
    Delivery driver with real-time location tracking.

    Linked to User model (role must be 'driver').
    """

    user = models.OneToOneField(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="driver_profile",
        limit_choices_to={"role": "driver"},
    )
    phone = models.CharField(
        max_length=20, help_text="Driver contact phone (may differ from user phone)"
    )
    vehicle_type = models.CharField(
        max_length=20, choices=VehicleType.choices, default=VehicleType.MOTORCYCLE
    )
    vehicle_plate = models.CharField(
        max_length=20, blank=True, help_text="License plate number"
    )

    # Availability status
    is_available = models.BooleanField(default=False)
    went_online_at = models.DateTimeField(null=True, blank=True)

    # Current location (updated in real-time)
    current_location = gis_models.PointField(
        geography=True, srid=4326, null=True, blank=True
    )
    location_updated_at = models.DateTimeField(null=True, blank=True)

    # Stats
    total_deliveries = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)

    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["user__name"]

    def __str__(self):
        return f"{self.user.name} ({self.vehicle_type})"

    def update_location(self, lat: float, lng: float):
        """Update driver's current location."""
        # GIS uses (lng, lat) order!
        self.current_location = Point(lng, lat, srid=4326)
        self.location_updated_at = timezone.now()
        self.save(update_fields=["current_location", "location_updated_at"])

    def go_online(self):
        """Mark driver as available for deliveries."""
        self.is_available = True
        self.went_online_at = timezone.now()
        self.save(update_fields=["is_available", "went_online_at"])

    def go_offline(self):
        """Mark driver as unavailable."""
        self.is_available = False
        self.went_online_at = None
        self.save(update_fields=["is_available", "went_online_at"])
