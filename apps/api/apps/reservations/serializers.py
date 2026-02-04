"""Serializers for reservations app."""

from datetime import date, datetime, timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import (
    BusinessHours,
    Reservation,
    ReservationSettings,
    ReservationSource,
    ReservationStatus,
    SpecialHours,
    TableConfiguration,
    Waitlist,
)


class TableConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for table configuration."""

    class Meta:
        model = TableConfiguration
        fields = [
            "id",
            "name",
            "capacity",
            "min_capacity",
            "location",
            "is_active",
            "display_order",
        ]


class BusinessHoursSerializer(serializers.ModelSerializer):
    """Serializer for business hours."""

    day_name = serializers.SerializerMethodField()

    class Meta:
        model = BusinessHours
        fields = [
            "id",
            "day_of_week",
            "day_name",
            "is_open",
            "open_time",
            "close_time",
            "last_seating_time",
        ]

    def get_day_name(self, obj):
        return dict(BusinessHours.DAY_CHOICES).get(obj.day_of_week, "Unknown")


class SpecialHoursSerializer(serializers.ModelSerializer):
    """Serializer for special hours."""

    class Meta:
        model = SpecialHours
        fields = [
            "id",
            "date",
            "is_closed",
            "open_time",
            "close_time",
            "reason",
        ]


class ReservationSettingsSerializer(serializers.ModelSerializer):
    """Serializer for reservation settings."""

    class Meta:
        model = ReservationSettings
        fields = [
            "min_advance_hours",
            "max_advance_days",
            "slot_duration_minutes",
            "default_dining_duration_minutes",
            "max_party_size",
            "require_phone",
            "require_email",
            "confirmation_required",
            "cancellation_hours",
            "no_show_threshold",
            "confirmation_message",
            "reminder_hours",
        ]


class ReservationSerializer(serializers.ModelSerializer):
    """Serializer for reservations."""

    table_name = serializers.CharField(source="table.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)
    end_time = serializers.TimeField(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id",
            "date",
            "time",
            "duration_minutes",
            "end_time",
            "party_size",
            "table",
            "table_name",
            "customer_name",
            "customer_phone",
            "customer_email",
            "status",
            "status_display",
            "source",
            "source_display",
            "special_requests",
            "occasion",
            "confirmation_code",
            "confirmed_at",
            "seated_at",
            "completed_at",
            "cancelled_at",
            "cancellation_reason",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "confirmation_code",
            "confirmed_at",
            "seated_at",
            "completed_at",
            "cancelled_at",
            "created_at",
        ]


class CreateReservationSerializer(serializers.ModelSerializer):
    """Serializer for creating reservations."""

    class Meta:
        model = Reservation
        fields = [
            "date",
            "time",
            "party_size",
            "customer_name",
            "customer_phone",
            "customer_email",
            "special_requests",
            "occasion",
        ]

    def validate_date(self, value):
        """Validate reservation date."""
        if value < date.today():
            raise serializers.ValidationError("Cannot book for past dates")

        settings = self.context.get("settings")
        if settings:
            max_date = date.today() + timedelta(days=settings.max_advance_days)
            if value > max_date:
                raise serializers.ValidationError(
                    f"Cannot book more than {settings.max_advance_days} days in advance"
                )

        return value

    def validate_party_size(self, value):
        """Validate party size."""
        settings = self.context.get("settings")
        if settings and value > settings.max_party_size:
            raise serializers.ValidationError(
                f"Party size cannot exceed {settings.max_party_size}"
            )
        return value

    def validate(self, data):
        """Validate the full booking."""
        settings = self.context.get("settings")

        # Check phone requirement
        if settings and settings.require_phone and not data.get("customer_phone"):
            raise serializers.ValidationError(
                {"customer_phone": "Phone number is required"}
            )

        # Check email requirement
        if settings and settings.require_email and not data.get("customer_email"):
            raise serializers.ValidationError(
                {"customer_email": "Email is required"}
            )

        # Check minimum advance time
        if settings:
            booking_dt = datetime.combine(data["date"], data["time"])
            min_booking_time = timezone.now() + timedelta(hours=settings.min_advance_hours)
            if booking_dt < min_booking_time.replace(tzinfo=None):
                raise serializers.ValidationError(
                    f"Reservations must be made at least {settings.min_advance_hours} hours in advance"
                )

        return data


class PublicCreateReservationSerializer(CreateReservationSerializer):
    """Serializer for public reservation creation (no auth required)."""

    pass


class ReservationStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating reservation status."""

    status = serializers.ChoiceField(choices=ReservationStatus.choices)
    cancellation_reason = serializers.CharField(required=False, allow_blank=True)


class WaitlistSerializer(serializers.ModelSerializer):
    """Serializer for waitlist entries."""

    class Meta:
        model = Waitlist
        fields = [
            "id",
            "customer_name",
            "customer_phone",
            "party_size",
            "is_notified",
            "is_seated",
            "is_cancelled",
            "estimated_wait_minutes",
            "notified_at",
            "seated_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "is_notified",
            "is_seated",
            "is_cancelled",
            "notified_at",
            "seated_at",
            "created_at",
        ]


class CreateWaitlistSerializer(serializers.ModelSerializer):
    """Serializer for adding to waitlist."""

    class Meta:
        model = Waitlist
        fields = [
            "customer_name",
            "customer_phone",
            "party_size",
            "estimated_wait_minutes",
        ]


class AvailabilitySlot(serializers.Serializer):
    """Serializer for available time slots."""

    time = serializers.TimeField()
    available_tables = serializers.IntegerField()
    max_party_size = serializers.IntegerField()


class AvailabilityRequestSerializer(serializers.Serializer):
    """Request serializer for availability check."""

    date = serializers.DateField()
    party_size = serializers.IntegerField(min_value=1)


class AvailabilityResponseSerializer(serializers.Serializer):
    """Response serializer for availability."""

    date = serializers.DateField()
    party_size = serializers.IntegerField()
    slots = AvailabilitySlot(many=True)
    is_available = serializers.BooleanField()


class DailyReservationSummary(serializers.Serializer):
    """Summary of reservations for a day."""

    date = serializers.DateField()
    total_reservations = serializers.IntegerField()
    total_guests = serializers.IntegerField()
    confirmed = serializers.IntegerField()
    pending = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    no_shows = serializers.IntegerField()
