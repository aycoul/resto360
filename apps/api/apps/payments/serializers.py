"""Serializers for payment models and API."""

from rest_framework import serializers

from .models import CashDrawerSession, Payment, PaymentMethod


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for PaymentMethod model."""

    class Meta:
        model = PaymentMethod
        fields = [
            "id",
            "provider_code",
            "name",
            "is_active",
            "display_order",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Set restaurant from request context."""
        request = self.context.get("request")
        if request and hasattr(request.user, "restaurant"):
            validated_data["restaurant"] = request.user.restaurant
        return super().create(validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "payment_method",
            "amount",
            "status",
            "provider_code",
            "provider_reference",
            "initiated_at",
            "completed_at",
            "refunded_amount",
        ]
        read_only_fields = [
            "id",
            "status",
            "provider_reference",
            "initiated_at",
            "completed_at",
            "refunded_amount",
        ]


class CashDrawerSessionSerializer(serializers.ModelSerializer):
    """Serializer for CashDrawerSession model."""

    cashier_name = serializers.CharField(source="cashier.get_full_name", read_only=True)
    cashier_phone = serializers.CharField(source="cashier.phone", read_only=True)
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = CashDrawerSession
        fields = [
            "id",
            "cashier",
            "cashier_name",
            "cashier_phone",
            "opened_at",
            "opening_balance",
            "closed_at",
            "closing_balance",
            "expected_balance",
            "variance",
            "variance_notes",
            "is_open",
        ]
        read_only_fields = [
            "id",
            "cashier",
            "cashier_name",
            "cashier_phone",
            "opened_at",
            "expected_balance",
            "variance",
            "is_open",
        ]


class OpenDrawerSerializer(serializers.Serializer):
    """Serializer for opening a cash drawer session."""

    opening_balance = serializers.IntegerField(min_value=0, required=True)


class CloseDrawerSerializer(serializers.Serializer):
    """Serializer for closing a cash drawer session."""

    closing_balance = serializers.IntegerField(min_value=0, required=True)
    variance_notes = serializers.CharField(required=False, allow_blank=True, default="")


class InitiatePaymentSerializer(serializers.Serializer):
    """Serializer for initiating a payment."""

    order_id = serializers.UUIDField(
        required=True,
        help_text="UUID of the order to pay",
    )
    provider_code = serializers.CharField(
        required=True,
        max_length=20,
        help_text="Payment provider code (wave, orange, mtn, cash)",
    )
    idempotency_key = serializers.CharField(
        required=True,
        max_length=255,
        help_text="Unique key to prevent duplicate payments",
    )
    callback_url = serializers.URLField(
        required=False,
        allow_blank=True,
        default="",
        help_text="URL for webhook notifications",
    )
    success_url = serializers.URLField(
        required=False,
        allow_blank=True,
        default="",
        help_text="URL to redirect after successful payment",
    )
    error_url = serializers.URLField(
        required=False,
        allow_blank=True,
        default="",
        help_text="URL to redirect after failed payment",
    )


class PaymentStatusSerializer(serializers.Serializer):
    """Serializer for payment status response."""

    id = serializers.UUIDField(read_only=True)
    order_id = serializers.UUIDField(read_only=True)
    amount = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    provider_code = serializers.CharField(read_only=True)
    provider_reference = serializers.CharField(read_only=True)
    initiated_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    error_code = serializers.CharField(read_only=True, allow_blank=True)
    error_message = serializers.CharField(read_only=True, allow_blank=True)


class PaymentInitiateResponseSerializer(serializers.Serializer):
    """Serializer for payment initiation response."""

    payment = PaymentSerializer(read_only=True)
    redirect_url = serializers.URLField(read_only=True, allow_null=True)
    status = serializers.CharField(read_only=True)
    is_duplicate = serializers.BooleanField(read_only=True)


class RefundRequestSerializer(serializers.Serializer):
    """Serializer for refund request."""

    amount = serializers.IntegerField(
        required=False,
        min_value=1,
        allow_null=True,
        help_text="Refund amount in XOF (null or omit for full refund)",
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        default="",
        help_text="Reason for the refund",
    )


class ProviderBreakdownSerializer(serializers.Serializer):
    """Serializer for provider breakdown in reconciliation."""

    provider_code = serializers.CharField(read_only=True)
    provider_name = serializers.CharField(read_only=True)
    count = serializers.IntegerField(read_only=True)
    total = serializers.IntegerField(read_only=True)


class ReconciliationTotalsSerializer(serializers.Serializer):
    """Serializer for reconciliation totals."""

    count = serializers.IntegerField(read_only=True)
    amount = serializers.IntegerField(read_only=True)


class ReconciliationSerializer(serializers.Serializer):
    """Serializer for daily reconciliation report."""

    date = serializers.DateField(read_only=True)
    restaurant_id = serializers.UUIDField(read_only=True)
    by_provider = ProviderBreakdownSerializer(many=True, read_only=True)
    totals = ReconciliationTotalsSerializer(read_only=True)
    refunds = ReconciliationTotalsSerializer(read_only=True)
    pending = ReconciliationTotalsSerializer(read_only=True)
    failed = ReconciliationTotalsSerializer(read_only=True)
    net_amount = serializers.IntegerField(read_only=True)


class RefundResponseSerializer(serializers.Serializer):
    """Serializer for refund response."""

    success = serializers.BooleanField(read_only=True)
    refund_type = serializers.CharField(read_only=True, allow_null=True)
    refunded_amount = serializers.IntegerField(read_only=True, allow_null=True)
    provider_reference = serializers.CharField(read_only=True, allow_null=True)
    error = serializers.CharField(read_only=True, allow_null=True)
