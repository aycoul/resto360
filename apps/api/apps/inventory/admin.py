from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import MenuItemIngredient, StockItem, StockMovement


@admin.register(StockItem)
class StockItemAdmin(SimpleHistoryAdmin):
    """Admin for StockItem with history tracking."""

    list_display = [
        "name",
        "sku",
        "restaurant",
        "current_quantity",
        "unit",
        "low_stock_threshold",
        "is_low_stock",
        "is_active",
    ]
    list_filter = ["restaurant", "unit", "is_active"]
    search_fields = ["name", "sku"]
    ordering = ["restaurant", "name"]
    readonly_fields = ["current_quantity", "low_stock_alert_sent"]

    def is_low_stock(self, obj):
        """Display low stock status."""
        return obj.is_low_stock

    is_low_stock.boolean = True
    is_low_stock.short_description = "Low Stock"


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Admin for StockMovement (read-only - movements are immutable)."""

    list_display = [
        "stock_item",
        "restaurant",
        "quantity_change",
        "movement_type",
        "reason",
        "balance_after",
        "created_by",
        "created_at",
    ]
    list_filter = ["restaurant", "movement_type", "reason", "created_at"]
    search_fields = ["stock_item__name", "notes"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    def has_change_permission(self, request, obj=None):
        """Prevent editing - movements are immutable."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - movements are immutable audit records."""
        return False


@admin.register(MenuItemIngredient)
class MenuItemIngredientAdmin(admin.ModelAdmin):
    """Admin for recipe ingredient mappings."""

    list_display = [
        "menu_item",
        "stock_item",
        "quantity_required",
        "restaurant",
    ]
    list_filter = ["restaurant", "stock_item"]
    search_fields = ["menu_item__name", "stock_item__name"]
    autocomplete_fields = ["menu_item", "stock_item"]
    ordering = ["restaurant", "menu_item__name", "stock_item__name"]
