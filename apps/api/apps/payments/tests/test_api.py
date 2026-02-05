"""API integration tests for payment endpoints."""

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status

from apps.payments.models import Payment, PaymentStatus
from apps.payments.providers.base import PaymentResult, ProviderStatus


@pytest.mark.django_db
class TestPaymentInitiate:
    """Tests for POST /api/payments/initiate/"""

    def test_initiate_cash_payment(self, owner_client, owner, sample_payment_method):
        """Cash payments complete immediately with SUCCESS status."""
        from apps.orders.tests.factories import OrderFactory

        order = OrderFactory(business=owner.business, cashier=owner, total=15000)

        url = reverse("payment-initiate")
        data = {
            "order_id": str(order.id),
            "provider_code": "cash",
            "idempotency_key": f"cash_{uuid.uuid4().hex}",
        }

        response = owner_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == PaymentStatus.SUCCESS
        assert response.data["redirect_url"] is None
        assert response.data["is_duplicate"] is False
        assert response.data["payment"]["amount"] == 15000

        # Verify payment in database
        payment = Payment.all_objects.get(id=response.data["payment"]["id"])
        assert payment.status == PaymentStatus.SUCCESS
        assert payment.completed_at is not None

    @patch("apps.payments.providers.get_provider")
    def test_initiate_wave_payment(
        self, mock_get_provider, owner_client, owner, sample_payment_method
    ):
        """Wave payment returns redirect URL for customer."""
        from apps.orders.tests.factories import OrderFactory
        from apps.payments.tests.factories import PaymentMethodFactory

        # Create Wave payment method
        wave_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="wave",
            name="Wave",
            is_active=True,
        )

        order = OrderFactory(business=owner.business, cashier=owner, total=25000)

        # Mock provider
        mock_provider = MagicMock()
        mock_provider.initiate_payment.return_value = PaymentResult(
            provider_reference="wave_ref_123",
            status=ProviderStatus.PENDING,
            redirect_url="https://pay.wave.com/checkout/abc123",
            raw_response={"checkout_id": "abc123"},
        )
        mock_get_provider.return_value = mock_provider

        url = reverse("payment-initiate")
        data = {
            "order_id": str(order.id),
            "provider_code": "wave",
            "idempotency_key": f"wave_{uuid.uuid4().hex}",
        }

        response = owner_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == PaymentStatus.PROCESSING
        assert response.data["redirect_url"] == "https://pay.wave.com/checkout/abc123"
        assert response.data["is_duplicate"] is False

        # Verify provider was called
        mock_provider.initiate_payment.assert_called_once()

    def test_initiate_payment_idempotent(
        self, owner_client, owner, sample_payment_method
    ):
        """Same idempotency key returns existing payment."""
        from apps.orders.tests.factories import OrderFactory

        order = OrderFactory(business=owner.business, cashier=owner, total=10000)
        idempotency_key = f"idem_{uuid.uuid4().hex}"

        url = reverse("payment-initiate")
        data = {
            "order_id": str(order.id),
            "provider_code": "cash",
            "idempotency_key": idempotency_key,
        }

        # First request - creates payment
        response1 = owner_client.post(url, data, format="json")
        assert response1.status_code == status.HTTP_201_CREATED
        payment_id = response1.data["payment"]["id"]

        # Second request - returns existing payment
        response2 = owner_client.post(url, data, format="json")
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data["is_duplicate"] is True
        assert response2.data["payment"]["id"] == payment_id

        # Only one payment created
        assert (
            Payment.all_objects.filter(idempotency_key=idempotency_key).count() == 1
        )

    def test_initiate_payment_invalid_order(
        self, owner_client, owner, sample_payment_method
    ):
        """Returns 404 for non-existent order."""
        url = reverse("payment-initiate")
        data = {
            "order_id": str(uuid.uuid4()),  # Random UUID
            "provider_code": "cash",
            "idempotency_key": f"test_{uuid.uuid4().hex}",
        }

        response = owner_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Order not found" in response.data["detail"]

    def test_initiate_payment_inactive_method(self, owner_client, owner):
        """Returns 400 for inactive payment method."""
        from apps.orders.tests.factories import OrderFactory
        from apps.payments.tests.factories import PaymentMethodFactory

        # Create inactive payment method
        PaymentMethodFactory(
            business=owner.business,
            provider_code="wave",
            name="Wave (disabled)",
            is_active=False,
        )

        order = OrderFactory(business=owner.business, cashier=owner, total=5000)

        url = reverse("payment-initiate")
        data = {
            "order_id": str(order.id),
            "provider_code": "wave",
            "idempotency_key": f"test_{uuid.uuid4().hex}",
        }

        response = owner_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found or inactive" in response.data["detail"]


@pytest.mark.django_db
class TestPaymentStatus:
    """Tests for GET /api/payments/{id}/status/"""

    def test_get_payment_status(self, owner_client, owner, sample_payment):
        """Returns payment status for valid payment."""
        url = reverse("payment-get-status", kwargs={"pk": sample_payment.id})

        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(sample_payment.id)
        assert response.data["status"] == sample_payment.status
        assert response.data["amount"] == sample_payment.amount

    def test_get_payment_status_not_found(self, owner_client, owner):
        """Returns 404 for non-existent payment."""
        url = reverse("payment-get-status", kwargs={"pk": uuid.uuid4()})

        response = owner_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_payment_status_tenant_isolation(self, owner_client, owner):
        """Cannot access payments from other businesses."""
        from apps.authentication.tests.factories import BusinessFactory
        from apps.orders.tests.factories import OrderFactory
        from apps.payments.tests.factories import PaymentFactory, PaymentMethodFactory

        # Create payment for another business
        other_business = BusinessFactory()
        other_method = PaymentMethodFactory(
            business=other_business, provider_code="cash"
        )
        other_order = OrderFactory(business=other_business)
        other_payment = PaymentFactory(
            business=other_business,
            order=other_order,
            payment_method=other_method,
        )

        url = reverse("payment-get-status", kwargs={"pk": other_payment.id})

        response = owner_client.get(url)

        # Should not find the payment (tenant isolation)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestPaymentList:
    """Tests for GET /api/payments/"""

    def test_list_payments(self, owner_client, owner, sample_payment):
        """Returns list of payments for the business."""
        url = reverse("payment-list")

        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Response may be paginated (results key) or a direct list
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(results) >= 1
        # Find our sample payment
        payment_ids = [p["id"] for p in results]
        assert str(sample_payment.id) in payment_ids

    def test_list_payments_filter_by_status(self, owner_client, owner):
        """Can filter payments by status."""
        from apps.orders.tests.factories import OrderFactory
        from apps.payments.tests.factories import PaymentFactory, PaymentMethodFactory

        method = PaymentMethodFactory(business=owner.business, provider_code="cash")
        order = OrderFactory(business=owner.business, cashier=owner)

        # Create payments with different statuses
        pending_payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=method,
            status=PaymentStatus.PENDING,
        )
        success_payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=method,
            status=PaymentStatus.PENDING,
        )
        # Transition success_payment to SUCCESS
        success_payment.start_processing()
        success_payment.mark_success()
        success_payment.save()

        # Filter by SUCCESS status
        url = reverse("payment-list")
        response = owner_client.get(url, {"status": PaymentStatus.SUCCESS})

        assert response.status_code == status.HTTP_200_OK
        # Response may be paginated (results key) or a direct list
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        # All returned payments should be SUCCESS
        for payment_data in results:
            assert payment_data["status"] == PaymentStatus.SUCCESS


@pytest.mark.django_db
class TestWebhooks:
    """Tests for webhook endpoints."""

    @patch("apps.payments.views.process_webhook_event.delay")
    def test_webhook_wave_success(self, mock_delay, api_client):
        """Wave webhook is received and queued."""
        url = reverse("webhook-wave")
        data = {
            "event_type": "checkout.session.completed",
            "data": {
                "id": "cs_test_123",
                "client_reference": "order_123",
            },
        }

        response = api_client.post(
            url,
            json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["received"] is True

        # Verify task was queued
        mock_delay.assert_called_once()
        call_args = mock_delay.call_args
        assert call_args.kwargs["provider_code"] == "wave"

    @patch("apps.payments.views.process_webhook_event.delay")
    def test_webhook_orange(self, mock_delay, api_client):
        """Orange webhook is received and queued."""
        url = reverse("webhook-orange")
        data = {
            "status": "SUCCESSFULL",
            "txnid": "orange_123",
        }

        response = api_client.post(
            url,
            json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_delay.assert_called_once()
        assert mock_delay.call_args.kwargs["provider_code"] == "orange"

    @patch("apps.payments.views.process_webhook_event.delay")
    def test_webhook_mtn(self, mock_delay, api_client):
        """MTN webhook is received and queued."""
        url = reverse("webhook-mtn")
        data = {
            "financialTransactionId": "mtn_123",
            "status": "SUCCESSFUL",
        }

        response = api_client.post(
            url,
            json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_delay.assert_called_once()
        assert mock_delay.call_args.kwargs["provider_code"] == "mtn"

    def test_webhook_no_auth_required(self, api_client):
        """Webhooks don't require authentication."""
        url = reverse("webhook-wave")

        # POST without authentication
        response = api_client.post(
            url,
            "{}",
            content_type="application/json",
        )

        # Should not return 401 or 403
        assert response.status_code == status.HTTP_200_OK

    @patch("apps.payments.views.process_webhook_event.delay")
    def test_webhook_invalid_signature_still_accepted(self, mock_delay, api_client):
        """
        Webhook is accepted even with invalid signature.

        Signature verification happens in the async task, not the webhook view.
        This ensures we always return 200 quickly to the provider.
        """
        url = reverse("webhook-wave")

        # Send with wrong signature header
        response = api_client.post(
            url,
            json.dumps({"event": "test"}),
            content_type="application/json",
            HTTP_WAVE_SIGNATURE="invalid_signature",
        )

        # View accepts it (verification happens in task)
        assert response.status_code == status.HTTP_200_OK
        mock_delay.assert_called_once()


@pytest.mark.django_db
class TestPaymentAuthRequired:
    """Tests that payment endpoints require authentication."""

    def test_initiate_requires_auth(self, api_client):
        """POST /api/payments/initiate/ requires authentication."""
        url = reverse("payment-initiate")

        response = api_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_requires_auth(self, api_client):
        """GET /api/payments/ requires authentication."""
        url = reverse("payment-list")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_status_requires_auth(self, api_client):
        """GET /api/payments/{id}/status/ requires authentication."""
        url = reverse("payment-get-status", kwargs={"pk": uuid.uuid4()})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
