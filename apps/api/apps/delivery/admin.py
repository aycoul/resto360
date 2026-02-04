"""Admin configuration for delivery models."""

from django.contrib.gis import admin

from .models import DeliveryZone, Driver


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.GISModelAdmin):
    """Admin for delivery zones with map widget."""

    list_display = ["name", "restaurant", "delivery_fee", "minimum_order", "is_active"]
    list_filter = ["restaurant", "is_active"]
    search_fields = ["name", "restaurant__name"]


@admin.register(Driver)
class DriverAdmin(admin.GISModelAdmin):
    """Admin for drivers with location map."""

    list_display = [
        "user",
        "restaurant",
        "vehicle_type",
        "is_available",
        "total_deliveries",
    ]
    list_filter = ["restaurant", "is_available", "vehicle_type"]
    search_fields = ["user__name", "user__phone"]
    readonly_fields = ["total_deliveries", "average_rating", "location_updated_at"]
