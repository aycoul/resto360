"""
Serializers for the Supplier Marketplace API.
"""

from decimal import Decimal

from rest_framework import serializers

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


class SupplierCategorySerializer(serializers.ModelSerializer):
    """Serializer for supplier categories."""

    subcategories = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = SupplierCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "icon",
            "image",
            "parent",
            "subcategories",
            "product_count",
            "display_order",
        ]

    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return SupplierCategorySerializer(
                obj.subcategories.filter(is_active=True),
                many=True,
            ).data
        return []

    def get_product_count(self, obj):
        return obj.products.filter(is_available=True, supplier__is_active=True).count()


class SupplierListSerializer(serializers.ModelSerializer):
    """Serializer for listing suppliers."""

    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "supplier_type",
            "city",
            "country",
            "logo",
            "verification_status",
            "minimum_order_value",
            "lead_time_days",
            "average_rating",
            "review_count",
            "product_count",
            "is_featured",
        ]

    def get_product_count(self, obj):
        return obj.products.filter(is_available=True).count()


class SupplierDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for a single supplier."""

    categories = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "supplier_type",
            "email",
            "phone",
            "website",
            "whatsapp",
            "address",
            "city",
            "region",
            "country",
            "logo",
            "cover_image",
            "verification_status",
            "years_in_business",
            "minimum_order_value",
            "delivery_areas",
            "delivery_days",
            "lead_time_days",
            "accepted_payment_methods",
            "payment_terms",
            "average_rating",
            "review_count",
            "total_orders",
            "is_featured",
            "categories",
            "is_favorite",
            "created_at",
        ]

    def get_categories(self, obj):
        categories = SupplierCategory.objects.filter(
            products__supplier=obj,
            products__is_available=True,
        ).distinct()
        return SupplierCategorySerializer(categories, many=True).data

    def get_is_favorite(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        restaurant = getattr(request.user, "restaurant", None)
        if not restaurant:
            return False
        return SupplierFavorite.objects.filter(
            restaurant=restaurant,
            supplier=obj,
        ).exists()


class SupplierCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating suppliers."""

    class Meta:
        model = Supplier
        fields = [
            "name",
            "slug",
            "description",
            "supplier_type",
            "email",
            "phone",
            "website",
            "whatsapp",
            "address",
            "city",
            "region",
            "country",
            "postal_code",
            "logo",
            "cover_image",
            "business_registration",
            "tax_id",
            "years_in_business",
            "minimum_order_value",
            "delivery_areas",
            "delivery_days",
            "lead_time_days",
            "accepted_payment_methods",
            "payment_terms",
        ]


class SupplierProductListSerializer(serializers.ModelSerializer):
    """Serializer for listing products."""

    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = SupplierProduct
        fields = [
            "id",
            "supplier",
            "supplier_name",
            "category",
            "category_name",
            "name",
            "slug",
            "description",
            "unit",
            "unit_size",
            "price",
            "minimum_order_quantity",
            "is_available",
            "stock_status",
            "image",
            "origin",
            "brand",
            "certifications",
        ]


class SupplierProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for a single product."""

    supplier = SupplierListSerializer(read_only=True)
    category = SupplierCategorySerializer(read_only=True)

    class Meta:
        model = SupplierProduct
        fields = [
            "id",
            "supplier",
            "category",
            "name",
            "slug",
            "description",
            "sku",
            "unit",
            "unit_size",
            "price",
            "bulk_pricing",
            "minimum_order_quantity",
            "order_increment",
            "is_available",
            "stock_status",
            "lead_time_days",
            "image",
            "images",
            "origin",
            "brand",
            "certifications",
            "times_ordered",
            "created_at",
        ]


class SupplierProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products."""

    class Meta:
        model = SupplierProduct
        fields = [
            "category",
            "name",
            "slug",
            "description",
            "sku",
            "unit",
            "unit_size",
            "price",
            "bulk_pricing",
            "minimum_order_quantity",
            "order_increment",
            "is_available",
            "stock_status",
            "lead_time_days",
            "image",
            "images",
            "origin",
            "brand",
            "certifications",
        ]


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items."""

    product = SupplierProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_id",
            "quantity",
            "unit_price",
            "line_total",
        ]


class CartSerializer(serializers.ModelSerializer):
    """Serializer for shopping carts."""

    supplier = SupplierListSerializer(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "supplier",
            "items",
            "total",
            "item_count",
            "created_at",
            "updated_at",
        ]


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart."""

    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity."""

    quantity = serializers.IntegerField(min_value=0)


class SupplierOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""

    class Meta:
        model = SupplierOrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "unit",
            "unit_size",
            "quantity",
            "quantity_received",
            "unit_price",
            "line_total",
            "notes",
        ]


class SupplierOrderListSerializer(serializers.ModelSerializer):
    """Serializer for listing orders."""

    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = SupplierOrder
        fields = [
            "id",
            "order_number",
            "supplier",
            "supplier_name",
            "restaurant",
            "restaurant_name",
            "status",
            "payment_status",
            "total",
            "item_count",
            "expected_delivery",
            "created_at",
        ]

    def get_item_count(self, obj):
        return obj.items.count()


class SupplierOrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for orders."""

    supplier = SupplierListSerializer(read_only=True)
    items = SupplierOrderItemSerializer(many=True, read_only=True)
    placed_by_name = serializers.CharField(source="placed_by.get_full_name", read_only=True)

    class Meta:
        model = SupplierOrder
        fields = [
            "id",
            "order_number",
            "supplier",
            "status",
            "payment_status",
            "submitted_at",
            "confirmed_at",
            "expected_delivery",
            "delivered_at",
            "delivery_address",
            "delivery_instructions",
            "subtotal",
            "delivery_fee",
            "tax",
            "discount",
            "total",
            "amount_paid",
            "payment_method",
            "payment_reference",
            "restaurant_notes",
            "supplier_notes",
            "invoice_number",
            "invoice_file",
            "items",
            "placed_by_name",
            "created_at",
            "updated_at",
        ]


class CreateOrderFromCartSerializer(serializers.Serializer):
    """Serializer for creating an order from a cart."""

    supplier_id = serializers.UUIDField()
    delivery_address = serializers.CharField()
    delivery_instructions = serializers.CharField(required=False, allow_blank=True)
    expected_delivery = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class UpdateOrderStatusSerializer(serializers.Serializer):
    """Serializer for updating order status."""

    status = serializers.ChoiceField(choices=SupplierOrder.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True)


class SupplierReviewSerializer(serializers.ModelSerializer):
    """Serializer for supplier reviews."""

    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SupplierReview
        fields = [
            "id",
            "supplier",
            "restaurant_name",
            "order",
            "reviewed_by_name",
            "overall_rating",
            "quality_rating",
            "delivery_rating",
            "communication_rating",
            "value_rating",
            "title",
            "comment",
            "supplier_response",
            "response_at",
            "is_verified",
            "created_at",
        ]

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name() or obj.reviewed_by.phone_number
        return None


class CreateReviewSerializer(serializers.ModelSerializer):
    """Serializer for creating a review."""

    class Meta:
        model = SupplierReview
        fields = [
            "supplier",
            "order",
            "overall_rating",
            "quality_rating",
            "delivery_rating",
            "communication_rating",
            "value_rating",
            "title",
            "comment",
        ]


class SupplierResponseSerializer(serializers.Serializer):
    """Serializer for supplier response to a review."""

    response = serializers.CharField()


class SupplierFavoriteSerializer(serializers.ModelSerializer):
    """Serializer for supplier favorites."""

    supplier = SupplierListSerializer(read_only=True)

    class Meta:
        model = SupplierFavorite
        fields = [
            "id",
            "supplier",
            "notes",
            "created_at",
        ]


class AddFavoriteSerializer(serializers.Serializer):
    """Serializer for adding a supplier to favorites."""

    supplier_id = serializers.UUIDField()
    notes = serializers.CharField(required=False, allow_blank=True)


class SupplierStatsSerializer(serializers.Serializer):
    """Serializer for supplier statistics."""

    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=0)
    pending_orders = serializers.IntegerField()
    this_month_orders = serializers.IntegerField()
    this_month_revenue = serializers.DecimalField(max_digits=14, decimal_places=0)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=0)
    top_products = serializers.ListField()
    top_customers = serializers.ListField()


class MarketplaceSearchSerializer(serializers.Serializer):
    """Serializer for marketplace search parameters."""

    q = serializers.CharField(required=False, allow_blank=True)
    category = serializers.SlugField(required=False)
    supplier = serializers.UUIDField(required=False)
    city = serializers.CharField(required=False)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=0, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=0, required=False)
    in_stock = serializers.BooleanField(required=False)
    certifications = serializers.ListField(child=serializers.CharField(), required=False)
    sort_by = serializers.ChoiceField(
        choices=["price", "-price", "name", "-name", "popularity"],
        required=False,
        default="name",
    )
