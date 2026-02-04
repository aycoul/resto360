"""Tests for CashProvider."""

import pytest

from apps.payments.models import Payment, PaymentStatus
from apps.payments.providers.base import ProviderStatus, RefundResult
from apps.payments.providers.cash import CashProvider


class TestCashProvider:
    """Tests for CashProvider class."""

    def test_provider_code(self):
        """Test that provider code is 'cash'."""
        provider = CashProvider()
        assert provider.provider_code == "cash"

    def test_initiate_payment_instant_success(self):
        """Test that cash payments return SUCCESS immediately."""
        provider = CashProvider()
        result = provider.initiate_payment(
            amount=10000,
            currency="XOF",
            order_reference="ORD-001",
            customer_phone="+2250101010101",
            idempotency_key="idem-123",
            callback_url="https://example.com/callback",
            success_url="https://example.com/success",
            error_url="https://example.com/error",
        )

        assert result.status == ProviderStatus.SUCCESS
        assert result.provider_reference == "idem-123"
        assert result.redirect_url is None
        assert result.error_code is None
        assert result.error_message is None

    @pytest.mark.django_db
    def test_check_status_returns_current(self, sample_payment_method, owner):
        """Test that check_status returns current payment status from database."""
        from apps.orders.tests.factories import OrderFactory

        provider = CashProvider()
        order = OrderFactory(restaurant=owner.restaurant, cashier=owner)

        # Create a payment with SUCCESS status
        payment = Payment.all_objects.create(
            restaurant=owner.restaurant,
            order=order,
            payment_method=sample_payment_method,
            amount=15000,
            status=PaymentStatus.PENDING,
            idempotency_key="idem-status-check",
            provider_code="cash",
            provider_reference="cash-ref-123",
        )
        # Manually transition to success
        payment.start_processing()
        payment.mark_success()
        payment.save()

        result = provider.check_status("cash-ref-123")

        assert result.status == ProviderStatus.SUCCESS
        assert result.provider_reference == "cash-ref-123"

    @pytest.mark.django_db
    def test_check_status_not_found(self):
        """Test that check_status returns PENDING for non-existent payment."""
        provider = CashProvider()
        result = provider.check_status("nonexistent-ref")

        assert result.status == ProviderStatus.PENDING
        assert result.raw_response.get("note") == "Payment not found"

    def test_process_refund_succeeds(self):
        """Test that process_refund returns success."""
        provider = CashProvider()
        result = provider.process_refund(
            provider_reference="cash-ref-123",
            amount=5000,
        )

        assert isinstance(result, RefundResult)
        assert result.success is True
        assert result.error_message is None

    def test_verify_webhook_returns_true(self):
        """Test that verify_webhook returns True (cash has no webhooks)."""
        provider = CashProvider()
        result = provider.verify_webhook(
            headers={"Content-Type": "application/json"},
            body=b"{}",
        )

        assert result is True

    def test_parse_webhook_returns_empty(self):
        """Test that parse_webhook returns empty dict (cash has no webhooks)."""
        provider = CashProvider()
        result = provider.parse_webhook(body=b'{"event": "test"}')

        assert result == {}
