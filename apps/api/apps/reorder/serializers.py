"""Reorder serializers for BIZ360."""

from rest_framework import serializers

from apps.menu.serializers import ProductSerializer
from apps.orders.serializers import OrderSerializer

from .models import CustomerProfile, OrderHistory, ReorderQRCode, ReorderScan


class ReorderQRCodeSerializer(serializers.ModelSerializer):
    """Serializer for reorder QR codes."""

    product = ProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    qr_url = serializers.SerializerMethodField()
    conversion_rate = serializers.SerializerMethodField()

    class Meta:
        model = ReorderQRCode
        fields = [
            "id",
            "code",
            "product",
            "product_id",
            "default_quantity",
            "min_quantity",
            "max_quantity",
            "require_name",
            "require_phone",
            "require_address",
            "is_active",
            "scan_count",
            "order_count",
            "conversion_rate",
            "promo_message",
            "discount_percent",
            "qr_url",
            "created_at",
        ]
        read_only_fields = [
            "id", "code", "scan_count", "order_count", "created_at"
        ]

    def get_qr_url(self, obj):
        """Generate the reorder page URL."""
        from django.conf import settings
        base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        return f"{base_url}/reorder/{obj.code}"

    def get_conversion_rate(self, obj):
        """Calculate scan to order conversion rate."""
        if obj.scan_count > 0:
            return round(obj.order_count / obj.scan_count * 100, 1)
        return 0

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["business"] = request.user.business
        validated_data["product_id"] = validated_data.pop("product_id")
        return super().create(validated_data)


class ReorderScanSerializer(serializers.ModelSerializer):
    """Serializer for QR scan records."""

    product_name = serializers.CharField(source="qr_code.product.name", read_only=True)

    class Meta:
        model = ReorderScan
        fields = [
            "id",
            "qr_code",
            "product_name",
            "scanned_at",
            "converted_to_order",
            "order",
            "converted_at",
        ]
        read_only_fields = ["id", "scanned_at"]


class CustomerProfileSerializer(serializers.ModelSerializer):
    """Serializer for customer profiles."""

    class Meta:
        model = CustomerProfile
        fields = [
            "id",
            "phone",
            "email",
            "name",
            "default_address",
            "is_verified",
            "accepts_marketing",
            "total_orders",
            "total_spent",
            "last_order_at",
            "created_at",
        ]
        read_only_fields = [
            "id", "is_verified", "total_orders", "total_spent",
            "last_order_at", "created_at"
        ]


class CustomerLookupSerializer(serializers.Serializer):
    """Serializer for customer lookup by phone."""

    phone = serializers.CharField(max_length=20)


class OrderHistorySerializer(serializers.ModelSerializer):
    """Serializer for order history."""

    order = OrderSerializer(read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = OrderHistory
        fields = [
            "id",
            "business_name",
            "order",
            "order_total",
            "order_date",
            "item_count",
            "reorder_count",
            "last_reordered_at",
        ]


class OrderHistoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for order history list."""

    business_name = serializers.CharField(source="business.name", read_only=True)
    order_number = serializers.CharField(source="order.order_number", read_only=True)

    class Meta:
        model = OrderHistory
        fields = [
            "id",
            "business_name",
            "order_number",
            "order_total",
            "order_date",
            "item_count",
            "reorder_count",
        ]


class PublicReorderInfoSerializer(serializers.Serializer):
    """Public serializer for reorder page info (no auth required)."""

    product_name = serializers.CharField()
    product_description = serializers.CharField()
    product_price = serializers.IntegerField()
    product_image = serializers.URLField(allow_null=True)
    business_name = serializers.CharField()
    business_logo = serializers.URLField(allow_null=True)
    default_quantity = serializers.IntegerField()
    min_quantity = serializers.IntegerField()
    max_quantity = serializers.IntegerField()
    require_name = serializers.BooleanField()
    require_phone = serializers.BooleanField()
    require_address = serializers.BooleanField()
    promo_message = serializers.CharField(allow_blank=True)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2)


class ReorderSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a reorder from QR scan."""

    code = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    customer_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=20)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    customer_address = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    # Payment info (for mobile money)
    payment_method = serializers.ChoiceField(
        choices=["wave", "orange_money", "mtn_momo", "cash"],
        default="cash",
    )


class ReorderFromHistorySerializer(serializers.Serializer):
    """Serializer for reordering from order history."""

    order_history_id = serializers.UUIDField()
    customer_phone = serializers.CharField(max_length=20)
    customer_address = serializers.CharField(required=False, allow_blank=True)
    # Allow quantity adjustments
    item_quantities = serializers.DictField(
        child=serializers.IntegerField(min_value=0),
        required=False,
        help_text="Map of order_item_id to new quantity (0 to remove)",
    )
