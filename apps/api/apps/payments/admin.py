"""Admin configuration for payments app."""

from django.contrib import admin

from .models import CashDrawerSession, Payment, PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Admin for PaymentMethod."""

    list_display = [
        "name",
        "provider_code",
        "restaurant",
        "is_active",
        "display_order",
    ]
    list_filter = ["restaurant", "provider_code", "is_active"]
    search_fields = ["name", "provider_code"]
    ordering = ["restaurant", "display_order", "name"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for Payment."""

    list_display = [
        "idempotency_key",
        "order",
        "restaurant",
        "amount",
        "status",
        "provider_code",
        "provider_reference",
        "initiated_at",
        "completed_at",
    ]
    list_filter = ["restaurant", "status", "provider_code", "initiated_at"]
    search_fields = ["idempotency_key", "provider_reference", "order__order_number"]
    ordering = ["-initiated_at"]
    date_hierarchy = "initiated_at"
    readonly_fields = [
        "status",
        "idempotency_key",
        "provider_response",
        "initiated_at",
        "completed_at",
    ]

    def has_change_permission(self, request, obj=None):
        """Prevent editing payments - they should be immutable."""
        return False


@admin.register(CashDrawerSession)
class CashDrawerSessionAdmin(admin.ModelAdmin):
    """Admin for CashDrawerSession."""

    list_display = [
        "cashier",
        "restaurant",
        "opened_at",
        "opening_balance",
        "closed_at",
        "closing_balance",
        "expected_balance",
        "variance",
        "is_open",
    ]
    list_filter = ["restaurant", "cashier", "opened_at"]
    search_fields = ["cashier__phone", "cashier__full_name"]
    ordering = ["-opened_at"]
    date_hierarchy = "opened_at"
    readonly_fields = ["opened_at", "expected_balance", "variance"]

    def is_open(self, obj):
        """Display whether the session is open."""
        return obj.is_open

    is_open.boolean = True
    is_open.short_description = "Open"
