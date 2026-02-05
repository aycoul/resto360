"""Admin configuration for orders app."""

from django.contrib import admin

from .models import DailySequence, Order, OrderItem, OrderItemModifier, Table


class OrderItemModifierInline(admin.TabularInline):
    model = OrderItemModifier
    extra = 0
    readonly_fields = ["modifier_option", "name", "price_adjustment"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["menu_item", "name", "unit_price", "quantity", "modifiers_total", "line_total"]
    show_change_link = True


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ["number", "business", "capacity", "is_active"]
    list_filter = ["business", "is_active"]
    search_fields = ["number"]


@admin.register(DailySequence)
class DailySequenceAdmin(admin.ModelAdmin):
    list_display = ["business", "date", "last_number"]
    list_filter = ["business", "date"]
    date_hierarchy = "date"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "business",
        "order_type",
        "status",
        "total",
        "cashier",
        "created_at",
    ]
    list_filter = ["business", "status", "order_type", "created_at"]
    search_fields = ["order_number", "customer_name", "customer_phone"]
    readonly_fields = ["order_number", "subtotal", "total"]
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "quantity", "unit_price", "line_total"]
    list_filter = ["order__business"]
    search_fields = ["name", "order__order_number"]
    inlines = [OrderItemModifierInline]
