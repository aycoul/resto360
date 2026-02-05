"""Tests for payment refund functionality."""

from unittest.mock import MagicMock, patch

import pytest

from apps.payments.models import Payment, PaymentStatus
from apps.payments.providers.base import RefundResult
from apps.payments.services import process_refund_request
from apps.payments.tests.factories import PaymentFactory, PaymentMethodFactory


@pytest.mark.django_db
class TestRefundService:
    """Tests for process_refund_request service."""

    def test_refund_cash_full(self, owner):
        """Test full refund for cash payment."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="cash",
            name="Cash",
        )

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=payment_method,
            amount=10000,
            provider_code="cash",
            idempotency_key="idem-refund-full",
        )
        payment.start_processing()
        payment.mark_success()
        payment.save()

        # Get fresh instance from DB (FSM protected fields don't like refresh_from_db)
        payment = Payment.all_objects.get(pk=payment.pk)

        # Process full refund (amount=None)
        result = process_refund_request(payment, amount=None, reason="Customer request")

        assert result["success"] is True
        assert result["refund_type"] == "full"
        assert result["refunded_amount"] == 10000

        # Check payment state
        payment = Payment.all_objects.get(pk=payment.pk)
        assert payment.status == PaymentStatus.REFUNDED
        assert payment.refunded_amount == 10000
        assert payment.provider_response["refund_reason"] == "Customer request"

    def test_refund_cash_partial(self, owner):
        """Test partial refund for cash payment."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="cash",
            name="Cash",
        )

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=payment_method,
            amount=10000,
            provider_code="cash",
            idempotency_key="idem-refund-partial",
        )
        payment.start_processing()
        payment.mark_success()
        payment.save()

        # Get fresh instance and refund 3000
        payment = Payment.all_objects.get(pk=payment.pk)
        result = process_refund_request(payment, amount=3000, reason="Partial refund")

        assert result["success"] is True
        assert result["refund_type"] == "partial"
        assert result["refunded_amount"] == 3000

        # Check payment state
        payment = Payment.all_objects.get(pk=payment.pk)
        assert payment.status == PaymentStatus.PARTIALLY_REFUNDED
        assert payment.refunded_amount == 3000

    @patch("apps.payments.providers.get_provider")
    def test_refund_mobile_money(self, mock_get_provider, owner):
        """Test refund for mobile money payment via provider."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="wave",
            name="Wave",
        )

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=payment_method,
            amount=10000,
            provider_code="wave",
            provider_reference="wave-ref-123",
            idempotency_key="idem-refund-wave",
        )
        payment.start_processing()
        payment.mark_success()
        payment.save()

        # Mock provider
        mock_provider = MagicMock()
        mock_provider.process_refund.return_value = RefundResult(
            success=True,
            provider_reference="refund-ref-456",
        )
        mock_get_provider.return_value = mock_provider

        # Get fresh instance and refund
        payment = Payment.all_objects.get(pk=payment.pk)
        result = process_refund_request(payment, amount=None, reason="Mobile refund")

        assert result["success"] is True
        assert result["refund_type"] == "full"
        assert result["provider_reference"] == "refund-ref-456"

        # Verify provider was called
        mock_provider.process_refund.assert_called_once_with("wave-ref-123", 10000)

    def test_refund_exceeds_amount(self, owner):
        """Test that refund amount exceeding payment is rejected."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="cash",
            name="Cash",
        )

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=payment_method,
            amount=10000,
            provider_code="cash",
            idempotency_key="idem-refund-exceed",
        )
        payment.start_processing()
        payment.mark_success()
        payment.save()

        # Try to refund 15000 on 10000 payment
        payment = Payment.all_objects.get(pk=payment.pk)
        result = process_refund_request(payment, amount=15000)

        assert result["success"] is False
        assert "exceeds" in result["error"]

    def test_refund_already_refunded(self, owner):
        """Test that fully refunded payment cannot be refunded again."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="cash",
            name="Cash",
        )

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=payment_method,
            amount=10000,
            provider_code="cash",
            idempotency_key="idem-refund-again",
        )
        payment.start_processing()
        payment.mark_success()
        payment.mark_refunded()
        payment.save()

        # Try to refund again
        payment = Payment.all_objects.get(pk=payment.pk)
        result = process_refund_request(payment, amount=None)

        assert result["success"] is False
        assert "status" in result["error"]

    def test_refund_pending_payment(self, owner):
        """Test that pending payment cannot be refunded."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="wave",
            name="Wave",
        )

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=payment_method,
            amount=10000,
            provider_code="wave",
            idempotency_key="idem-refund-pending",
        )
        payment.start_processing()
        payment.save()  # Still PROCESSING, not SUCCESS

        # Try to refund
        payment = Payment.all_objects.get(pk=payment.pk)
        result = process_refund_request(payment, amount=None)

        assert result["success"] is False
        assert "status" in result["error"]

    def test_multiple_partial_refunds(self, owner):
        """Test multiple partial refunds accumulate correctly."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="cash",
            name="Cash",
        )

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=payment_method,
            amount=10000,
            provider_code="cash",
            idempotency_key="idem-refund-multi",
        )
        payment.start_processing()
        payment.mark_success()
        payment.save()

        # First partial refund: 3000
        payment = Payment.all_objects.get(pk=payment.pk)
        result1 = process_refund_request(payment, amount=3000)
        assert result1["success"] is True
        assert result1["refunded_amount"] == 3000

        payment = Payment.all_objects.get(pk=payment.pk)
        assert payment.status == PaymentStatus.PARTIALLY_REFUNDED
        assert payment.refunded_amount == 3000

        # Second partial refund: 4000
        result2 = process_refund_request(payment, amount=4000)
        assert result2["success"] is True
        assert result2["refunded_amount"] == 4000

        payment = Payment.all_objects.get(pk=payment.pk)
        assert payment.status == PaymentStatus.PARTIALLY_REFUNDED
        assert payment.refunded_amount == 7000

        # Final refund: remaining 3000 (becomes full refund)
        result3 = process_refund_request(payment, amount=3000)
        assert result3["success"] is True
        assert result3["refund_type"] == "full"

        payment = Payment.all_objects.get(pk=payment.pk)
        assert payment.status == PaymentStatus.REFUNDED
        assert payment.refunded_amount == 10000

    def test_refund_zero_amount(self, owner):
        """Test that zero refund amount is rejected."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="cash",
            name="Cash",
        )

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=payment_method,
            amount=10000,
            provider_code="cash",
            idempotency_key="idem-refund-zero",
        )
        payment.start_processing()
        payment.mark_success()
        payment.save()

        # Try to refund 0
        payment = Payment.all_objects.get(pk=payment.pk)
        result = process_refund_request(payment, amount=0)

        assert result["success"] is False
        assert "positive" in result["error"]


@pytest.mark.django_db
class TestRefundAPI:
    """Tests for refund API endpoint."""

    def test_refund_api(self, owner_client, owner):
        """Test refund via API endpoint."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="cash",
            name="Cash",
        )

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=payment_method,
            amount=10000,
            provider_code="cash",
            idempotency_key="idem-api-refund",
        )
        payment.start_processing()
        payment.mark_success()
        payment.save()
        payment_id = payment.id

        response = owner_client.post(
            f"/api/v1/payments/{payment_id}/refund/",
            {"amount": 5000, "reason": "API test refund"},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["refund_type"] == "partial"
        assert response.data["refunded_amount"] == 5000

        # Verify payment state (get fresh instance)
        payment = Payment.all_objects.get(pk=payment_id)
        assert payment.status == PaymentStatus.PARTIALLY_REFUNDED
        assert payment.refunded_amount == 5000

    def test_refund_api_full_refund(self, owner_client, owner):
        """Test full refund via API (no amount specified)."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="cash",
            name="Cash",
        )

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=payment_method,
            amount=8000,
            provider_code="cash",
            idempotency_key="idem-api-full-refund",
        )
        payment.start_processing()
        payment.mark_success()
        payment.save()

        # Request refund without amount (full refund)
        response = owner_client.post(
            f"/api/v1/payments/{payment.id}/refund/",
            {"reason": "Full refund test"},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["refund_type"] == "full"
        assert response.data["refunded_amount"] == 8000

    def test_refund_api_not_found(self, owner_client):
        """Test refund for non-existent payment."""
        import uuid

        response = owner_client.post(
            f"/api/v1/payments/{uuid.uuid4()}/refund/",
            {"amount": 5000},
            format="json",
        )

        assert response.status_code == 404

    def test_refund_api_requires_auth(self, api_client, owner):
        """Test that refund requires authentication."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="cash",
            name="Cash",
        )

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=payment_method,
            amount=10000,
            provider_code="cash",
            idempotency_key="idem-api-unauth",
        )

        response = api_client.post(
            f"/api/v1/payments/{payment.id}/refund/",
            {"amount": 5000},
            format="json",
        )

        assert response.status_code == 401
