"""
Admin configuration for marketplace models.
"""

from django.contrib import admin

from .models import (
    Cart,
    CartItem,
    Supplier,
    SupplierCategory,
    SupplierFavorite,
    SupplierOrder,
    SupplierOrderItem,
    SupplierProduct,
    SupplierReview,
)


@admin.register(SupplierCategory)
class SupplierCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "display_order", "is_active"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "city",
        "supplier_type",
        "verification_status",
        "average_rating",
        "is_active",
    ]
    list_filter = ["verification_status", "supplier_type", "city", "is_active", "is_featured"]
    search_fields = ["name", "email", "phone"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["total_orders", "total_revenue", "average_rating", "review_count"]


@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ["name", "supplier", "category", "price", "stock_status", "is_available"]
    list_filter = ["supplier", "category", "stock_status", "is_available"]
    search_fields = ["name", "sku", "supplier__name"]
    prepopulated_fields = {"slug": ("name",)}


class SupplierOrderItemInline(admin.TabularInline):
    model = SupplierOrderItem
    extra = 0
    readonly_fields = ["line_total"]


@admin.register(SupplierOrder)
class SupplierOrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "supplier",
        "restaurant",
        "status",
        "payment_status",
        "total",
        "created_at",
    ]
    list_filter = ["status", "payment_status", "supplier"]
    search_fields = ["order_number", "restaurant__name", "supplier__name"]
    inlines = [SupplierOrderItemInline]
    readonly_fields = ["order_number", "subtotal", "total"]


@admin.register(SupplierReview)
class SupplierReviewAdmin(admin.ModelAdmin):
    list_display = [
        "supplier",
        "restaurant",
        "overall_rating",
        "is_verified",
        "is_published",
        "created_at",
    ]
    list_filter = ["overall_rating", "is_verified", "is_published"]
    search_fields = ["supplier__name", "restaurant__name", "comment"]


@admin.register(SupplierFavorite)
class SupplierFavoriteAdmin(admin.ModelAdmin):
    list_display = ["restaurant", "supplier", "created_at"]
    search_fields = ["restaurant__name", "supplier__name"]


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["restaurant", "supplier", "item_count", "total", "updated_at"]
    inlines = [CartItemInline]

    def item_count(self, obj):
        return obj.items.count()

    def total(self, obj):
        return obj.total
