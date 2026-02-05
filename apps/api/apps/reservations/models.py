"""Models for the reservations app."""

import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.core.models import TenantModel


class TableConfiguration(TenantModel):
    """
    Restaurant table configuration.

    Defines seating capacity and table arrangements.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, help_text="Table identifier (e.g., 'Table 1', 'Booth A')")
    capacity = models.PositiveIntegerField(help_text="Maximum number of guests")
    min_capacity = models.PositiveIntegerField(default=1, help_text="Minimum number of guests")
    location = models.CharField(
        max_length=50,
        blank=True,
        help_text="Location in business (e.g., 'Indoor', 'Terrace', 'Private Room')",
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Table"
        verbose_name_plural = "Tables"
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} (seats {self.capacity})"


class ReservationSettings(TenantModel):
    """
    Restaurant reservation settings.

    Configures booking rules and availability windows.
    """

    # Booking window
    min_advance_hours = models.PositiveIntegerField(
        default=1,
        help_text="Minimum hours in advance a reservation can be made",
    )
    max_advance_days = models.PositiveIntegerField(
        default=30,
        help_text="Maximum days in advance a reservation can be made",
    )

    # Time slots
    slot_duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Duration of each booking time slot",
    )
    default_dining_duration_minutes = models.PositiveIntegerField(
        default=90,
        help_text="Default dining duration for table turnover",
    )

    # Capacity
    max_party_size = models.PositiveIntegerField(
        default=10,
        help_text="Maximum party size for online booking",
    )
    require_phone = models.BooleanField(
        default=True,
        help_text="Require phone number for booking",
    )
    require_email = models.BooleanField(
        default=False,
        help_text="Require email for booking",
    )

    # Policies
    confirmation_required = models.BooleanField(
        default=False,
        help_text="Require business confirmation before booking is active",
    )
    cancellation_hours = models.PositiveIntegerField(
        default=2,
        help_text="Hours before reservation that cancellation is allowed",
    )
    no_show_threshold = models.PositiveIntegerField(
        default=3,
        help_text="Number of no-shows before customer is flagged",
    )

    # Messages
    confirmation_message = models.TextField(
        blank=True,
        help_text="Custom message to include in booking confirmation",
    )
    reminder_hours = models.PositiveIntegerField(
        default=24,
        help_text="Hours before reservation to send reminder",
    )

    class Meta:
        verbose_name = "Reservation Settings"
        verbose_name_plural = "Reservation Settings"

    def __str__(self):
        return f"Reservation Settings for {self.business.name}"


class BusinessHours(TenantModel):
    """
    Restaurant business hours for reservations.

    Defines when reservations can be made for each day.
    """

    DAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    day_of_week = models.PositiveIntegerField(choices=DAY_CHOICES)
    is_open = models.BooleanField(default=True)

    # Service periods (can have multiple per day, e.g., lunch and dinner)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    last_seating_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Last time reservations are accepted",
    )

    class Meta:
        verbose_name = "Business Hours"
        verbose_name_plural = "Business Hours"
        ordering = ["day_of_week", "open_time"]
        unique_together = [["business", "day_of_week", "open_time"]]

    def __str__(self):
        day_name = dict(self.DAY_CHOICES).get(self.day_of_week, "Unknown")
        if not self.is_open:
            return f"{day_name}: Closed"
        return f"{day_name}: {self.open_time} - {self.close_time}"


class SpecialHours(TenantModel):
    """
    Special hours for holidays or events.

    Overrides regular business hours for specific dates.
    """

    date = models.DateField()
    is_closed = models.BooleanField(default=False, help_text="Restaurant closed this day")
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    reason = models.CharField(max_length=100, blank=True, help_text="Reason for special hours")

    class Meta:
        verbose_name = "Special Hours"
        verbose_name_plural = "Special Hours"
        ordering = ["date"]
        unique_together = [["business", "date"]]

    def __str__(self):
        if self.is_closed:
            return f"{self.date}: Closed - {self.reason}"
        return f"{self.date}: {self.open_time} - {self.close_time}"


class ReservationStatus(models.TextChoices):
    """Status choices for reservations."""

    PENDING = "pending", "Pending Confirmation"
    CONFIRMED = "confirmed", "Confirmed"
    SEATED = "seated", "Seated"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No Show"


class ReservationSource(models.TextChoices):
    """Source of reservation."""

    ONLINE = "online", "Online Booking"
    PHONE = "phone", "Phone"
    WALK_IN = "walk_in", "Walk-in"
    THIRD_PARTY = "third_party", "Third Party"


class Reservation(TenantModel):
    """
    A table reservation.

    Tracks customer bookings and dining status.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Timing
    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=90)

    # Party details
    party_size = models.PositiveIntegerField()
    table = models.ForeignKey(
        TableConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations",
    )

    # Customer info
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
    )
    source = models.CharField(
        max_length=20,
        choices=ReservationSource.choices,
        default=ReservationSource.ONLINE,
    )

    # Special requests
    special_requests = models.TextField(blank=True)
    occasion = models.CharField(
        max_length=50,
        blank=True,
        help_text="Birthday, Anniversary, Business, etc.",
    )

    # Tracking
    confirmation_code = models.CharField(max_length=10, unique=True, editable=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    seated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    # Notifications
    reminder_sent = models.BooleanField(default=False)
    confirmation_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        ordering = ["date", "time"]
        indexes = [
            models.Index(fields=["business", "date", "status"]),
            models.Index(fields=["confirmation_code"]),
        ]

    def __str__(self):
        return f"{self.customer_name} - {self.date} {self.time} ({self.party_size} guests)"

    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = self._generate_confirmation_code()
        super().save(*args, **kwargs)

    def _generate_confirmation_code(self):
        """Generate a unique 6-character confirmation code."""
        import random
        import string

        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Reservation.all_objects.filter(confirmation_code=code).exists():
                return code

    @property
    def end_time(self):
        """Calculate reservation end time."""
        from datetime import datetime

        dt = datetime.combine(self.date, self.time)
        end_dt = dt + timedelta(minutes=self.duration_minutes)
        return end_dt.time()

    def confirm(self):
        """Confirm the reservation."""
        self.status = ReservationStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save()

    def seat(self):
        """Mark as seated."""
        self.status = ReservationStatus.SEATED
        self.seated_at = timezone.now()
        self.save()

    def complete(self):
        """Mark as completed."""
        self.status = ReservationStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    def cancel(self, reason=""):
        """Cancel the reservation."""
        self.status = ReservationStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save()

    def mark_no_show(self):
        """Mark as no-show."""
        self.status = ReservationStatus.NO_SHOW
        self.save()


class Waitlist(TenantModel):
    """
    Waitlist for walk-ins when no tables available.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Customer info
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    party_size = models.PositiveIntegerField()

    # Status
    is_notified = models.BooleanField(default=False)
    is_seated = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)

    # Timing
    estimated_wait_minutes = models.PositiveIntegerField(null=True, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True)
    seated_at = models.DateTimeField(null=True, blank=True)

    # Link to reservation if converted
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waitlist_entry",
    )

    class Meta:
        verbose_name = "Waitlist Entry"
        verbose_name_plural = "Waitlist"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.customer_name} ({self.party_size} guests)"

    def notify(self):
        """Mark as notified."""
        self.is_notified = True
        self.notified_at = timezone.now()
        self.save()

    def seat(self, reservation=None):
        """Mark as seated."""
        self.is_seated = True
        self.seated_at = timezone.now()
        if reservation:
            self.reservation = reservation
        self.save()

    def cancel(self):
        """Cancel waitlist entry."""
        self.is_cancelled = True
        self.save()
