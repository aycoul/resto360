from django.contrib import admin

from .models import CustomerProfile, OrderHistory, ReorderQRCode, ReorderScan


@admin.register(ReorderQRCode)
class ReorderQRCodeAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "business",
        "code",
        "default_quantity",
        "is_active",
        "scan_count",
        "order_count",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["product__name", "code"]
    readonly_fields = ["code", "scan_count", "order_count"]


@admin.register(ReorderScan)
class ReorderScanAdmin(admin.ModelAdmin):
    list_display = [
        "qr_code",
        "scanned_at",
        "converted_to_order",
        "ip_address",
    ]
    list_filter = ["converted_to_order", "scanned_at"]
    search_fields = ["qr_code__product__name"]
    readonly_fields = ["scanned_at"]


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = [
        "phone",
        "name",
        "email",
        "is_verified",
        "total_orders",
        "total_spent",
        "last_order_at",
    ]
    list_filter = ["is_verified", "accepts_marketing"]
    search_fields = ["phone", "name", "email"]
    readonly_fields = ["total_orders", "total_spent", "last_order_at"]


@admin.register(OrderHistory)
class OrderHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "customer",
        "business",
        "order",
        "order_total",
        "order_date",
        "reorder_count",
    ]
    list_filter = ["order_date"]
    search_fields = ["customer__phone", "customer__name"]
    readonly_fields = ["order_total", "order_date", "item_count", "reorder_count"]
