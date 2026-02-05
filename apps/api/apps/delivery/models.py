"""Delivery models for BIZ360 (formerly RESTO360)."""

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.db import models
from django.utils import timezone
from django_fsm import FSMField, transition

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
        return f"{self.name} ({self.business.name})"

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
            business=business, polygon__contains=point, is_active=True
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


class DeliveryStatus(models.TextChoices):
    """Delivery status enumeration."""

    PENDING_ASSIGNMENT = "pending_assignment", "Pending Assignment"
    ASSIGNED = "assigned", "Assigned"
    PICKED_UP = "picked_up", "Picked Up"
    EN_ROUTE = "en_route", "En Route"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"


class ProofType(models.TextChoices):
    """Proof of delivery type."""

    PHOTO = "photo", "Photo"
    SIGNATURE = "signature", "Signature"
    NONE = "none", "None"


class Delivery(TenantModel):
    """
    Delivery record linking order to driver.

    Status flow:
    pending_assignment -> assigned -> picked_up -> en_route -> delivered
                      \\-> cancelled (from any state)
    """

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="delivery",
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
    )
    zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
    )

    # Status with FSM
    status = FSMField(
        default=DeliveryStatus.PENDING_ASSIGNMENT,
        choices=DeliveryStatus.choices,
        protected=True,
    )

    # Addresses
    pickup_address = models.TextField(help_text="Restaurant address (copied at creation)")
    pickup_location = gis_models.PointField(
        geography=True,
        srid=4326,
        null=True,
        blank=True,
    )
    delivery_address = models.TextField(help_text="Customer delivery address")
    delivery_location = gis_models.PointField(
        geography=True,
        srid=4326,
        help_text="Customer delivery coordinates",
    )
    delivery_notes = models.TextField(
        blank=True,
        help_text="Delivery instructions from customer",
    )

    # Fees
    delivery_fee = models.PositiveIntegerField(help_text="Delivery fee charged in XOF")

    # Timestamps
    assigned_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    en_route_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_reason = models.TextField(blank=True)

    # Estimated time
    estimated_delivery_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Estimated time of delivery",
    )

    # Proof of delivery
    proof_type = models.CharField(
        max_length=20,
        choices=ProofType.choices,
        default=ProofType.NONE,
    )
    proof_photo = models.ImageField(
        upload_to="delivery_proofs/",
        null=True,
        blank=True,
    )
    proof_signature = models.TextField(
        blank=True,
        help_text="Base64-encoded signature image",
    )
    recipient_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of person who received delivery",
    )

    # Customer info (copied from order for quick access)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)

    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "deliveries"

    def __str__(self):
        return f"Delivery #{self.order.order_number}"

    # FSM Transitions

    @transition(
        field=status,
        source=DeliveryStatus.PENDING_ASSIGNMENT,
        target=DeliveryStatus.ASSIGNED,
    )
    def assign(self, driver: "Driver"):
        """Assign a driver to this delivery."""
        self.driver = driver
        self.assigned_at = timezone.now()

    @transition(
        field=status,
        source=DeliveryStatus.ASSIGNED,
        target=DeliveryStatus.PICKED_UP,
    )
    def mark_picked_up(self):
        """Driver has picked up the order from restaurant."""
        self.picked_up_at = timezone.now()

    @transition(
        field=status,
        source=DeliveryStatus.PICKED_UP,
        target=DeliveryStatus.EN_ROUTE,
    )
    def mark_en_route(self):
        """Driver is on the way to customer."""
        self.en_route_at = timezone.now()

    @transition(
        field=status,
        source=DeliveryStatus.EN_ROUTE,
        target=DeliveryStatus.DELIVERED,
    )
    def mark_delivered(
        self, proof_type: str, proof_data: str = "", recipient_name: str = ""
    ):
        """
        Mark delivery as complete with proof.

        Args:
            proof_type: 'photo' or 'signature'
            proof_data: Base64 image data (for signature) or will be set separately (for photo)
            recipient_name: Name of person who received
        """
        self.delivered_at = timezone.now()
        self.proof_type = proof_type
        self.recipient_name = recipient_name
        if proof_type == ProofType.SIGNATURE:
            self.proof_signature = proof_data

    @transition(
        field=status,
        source=[
            DeliveryStatus.PENDING_ASSIGNMENT,
            DeliveryStatus.ASSIGNED,
            DeliveryStatus.PICKED_UP,
            DeliveryStatus.EN_ROUTE,
        ],
        target=DeliveryStatus.CANCELLED,
    )
    def cancel(self, reason: str = ""):
        """Cancel this delivery."""
        self.cancelled_at = timezone.now()
        self.cancelled_reason = reason
        # Make driver available again if was assigned
        if self.driver and not self.driver.is_available:
            self.driver.go_online()
