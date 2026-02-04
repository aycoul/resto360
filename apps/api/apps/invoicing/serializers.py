"""Invoicing serializers for BIZ360."""

from rest_framework import serializers

from .models import DGIConfiguration, ElectronicInvoice, ElectronicInvoiceLine


class DGIConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for DGI configuration."""

    class Meta:
        model = DGIConfiguration
        fields = [
            "id",
            "taxpayer_id",
            "establishment_id",
            "is_production",
            "is_active",
            "last_sync_at",
            "last_error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_sync_at", "last_error", "created_at", "updated_at"]


class DGIConfigurationWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating DGI configuration."""

    class Meta:
        model = DGIConfiguration
        fields = [
            "taxpayer_id",
            "establishment_id",
            "api_key",
            "api_secret",
            "is_production",
            "is_active",
        ]
        extra_kwargs = {
            "api_key": {"write_only": True},
            "api_secret": {"write_only": True},
        }

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["business"] = request.user.business
        return super().create(validated_data)


class ElectronicInvoiceLineSerializer(serializers.ModelSerializer):
    """Serializer for invoice lines."""

    class Meta:
        model = ElectronicInvoiceLine
        fields = [
            "id",
            "description",
            "quantity",
            "unit_price_ht",
            "unit_price_ttc",
            "tva_rate",
            "tva_amount",
            "line_total_ht",
            "line_total_ttc",
        ]


class ElectronicInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for electronic invoices."""

    lines = ElectronicInvoiceLineSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    order_number = serializers.CharField(source="order.order_number", read_only=True)

    class Meta:
        model = ElectronicInvoice
        fields = [
            "id",
            "order",
            "order_number",
            "invoice_number",
            "invoice_date",
            "status",
            "status_display",
            # DGI fields
            "dgi_uid",
            "dgi_qr_code",
            "dgi_validation_date",
            "rejection_reason",
            # Amounts
            "subtotal_ht",
            "tva_rate",
            "tva_amount",
            "total_ttc",
            "discount_amount",
            # Seller
            "seller_name",
            "seller_ncc",
            "seller_address",
            # Customer
            "customer_name",
            "customer_ncc",
            "customer_address",
            "customer_phone",
            "customer_email",
            # Lines
            "lines",
            # Timestamps
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "dgi_uid", "dgi_qr_code", "dgi_signature",
            "dgi_validation_date", "status", "rejection_reason",
            "created_at", "updated_at",
        ]


class InvoiceCreateSerializer(serializers.Serializer):
    """Serializer for creating invoice from order."""

    order_id = serializers.UUIDField()
    submit_to_dgi = serializers.BooleanField(default=False)

    def validate_order_id(self, value):
        from apps.orders.models import Order
        request = self.context.get("request")
        try:
            order = Order.objects.get(id=value, business=request.user.business)
            return order
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")

    def create(self, validated_data):
        from .services import InvoiceService

        order = validated_data["order_id"]
        request = self.context.get("request")
        service = InvoiceService(request.user.business)

        # Create invoice
        invoice = service.create_invoice_from_order(order)

        # Submit to DGI if requested
        if validated_data.get("submit_to_dgi"):
            service.submit_to_dgi(invoice)

        return invoice


class InvoiceCancelSerializer(serializers.Serializer):
    """Serializer for cancelling an invoice."""

    reason = serializers.CharField(max_length=500)
