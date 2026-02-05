"""Tests for webhook verification and handlers."""

import hashlib
import hmac
import json
import time
from unittest.mock import patch

import pytest

from apps.payments.models import Payment, PaymentStatus
from apps.payments.webhooks.handlers import handle_wave_webhook
from apps.payments.webhooks.verification import verify_wave_signature

from .factories import PaymentFactory, PaymentMethodFactory


class TestWaveSignatureVerification:
    """Tests for Wave webhook signature verification."""

    @pytest.fixture
    def webhook_secret(self):
        """Return a test webhook secret."""
        return "whsec_test_secret_123"

    def generate_signature(self, timestamp: int, body: bytes, secret: str) -> str:
        """Generate a valid Wave signature header."""
        signed_payload = f"{timestamp}.".encode("utf-8") + body
        signature = hmac.new(
            key=secret.encode("utf-8"),
            msg=signed_payload,
            digestmod=hashlib.sha256,
        ).hexdigest()
        return f"t={timestamp},v1={signature}"

    def test_valid_signature_accepted(self, webhook_secret):
        """Test that valid signature is accepted."""
        body = b'{"type": "checkout.session.completed"}'
        timestamp = int(time.time())
        signature_header = self.generate_signature(timestamp, body, webhook_secret)

        headers = {"Wave-Signature": signature_header}

        result = verify_wave_signature(headers, body, webhook_secret)

        assert result is True

    def test_invalid_signature_rejected(self, webhook_secret):
        """Test that invalid signature is rejected."""
        body = b'{"type": "checkout.session.completed"}'
        timestamp = int(time.time())

        headers = {"Wave-Signature": f"t={timestamp},v1=invalidsignature"}

        result = verify_wave_signature(headers, body, webhook_secret)

        assert result is False

    def test_missing_signature_header_rejected(self, webhook_secret):
        """Test that missing signature header is rejected."""
        body = b'{"type": "checkout.session.completed"}'
        headers = {}

        result = verify_wave_signature(headers, body, webhook_secret)

        assert result is False

    def test_expired_timestamp_rejected(self, webhook_secret):
        """Test that expired timestamp is rejected."""
        body = b'{"type": "checkout.session.completed"}'
        # Timestamp 10 minutes ago
        timestamp = int(time.time()) - 600
        signature_header = self.generate_signature(timestamp, body, webhook_secret)

        headers = {"Wave-Signature": signature_header}

        result = verify_wave_signature(headers, body, webhook_secret, max_age_seconds=300)

        assert result is False

    def test_case_insensitive_header_name(self, webhook_secret):
        """Test that header name matching is case-insensitive."""
        body = b'{"type": "checkout.session.completed"}'
        timestamp = int(time.time())
        signature_header = self.generate_signature(timestamp, body, webhook_secret)

        # Lowercase header name
        headers = {"wave-signature": signature_header}

        result = verify_wave_signature(headers, body, webhook_secret)

        assert result is True

    def test_empty_secret_rejected(self):
        """Test that empty secret rejects webhook."""
        body = b'{"type": "checkout.session.completed"}'
        headers = {"Wave-Signature": "t=123,v1=abc"}

        result = verify_wave_signature(headers, body, "")

        assert result is False

    def test_malformed_signature_header_rejected(self, webhook_secret):
        """Test that malformed signature header is rejected."""
        body = b'{"type": "checkout.session.completed"}'

        # Missing v1
        headers = {"Wave-Signature": "t=123"}

        result = verify_wave_signature(headers, body, webhook_secret)

        assert result is False


@pytest.mark.django_db
class TestWaveWebhookHandler:
    """Tests for Wave webhook handler."""

    @pytest.fixture
    def wave_payment(self, owner):
        """Create a Wave payment in PROCESSING state."""
        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="wave",
            name="Wave",
        )
        payment = PaymentFactory(
            business=owner.business,
            payment_method=payment_method,
            provider_code="wave",
            provider_reference="checkout_123abc",
            amount=10000,
        )
        # Move to processing
        payment.start_processing()
        payment.save()
        return payment

    def test_handle_webhook_success(self, wave_payment):
        """Test handling successful payment webhook."""
        webhook_data = {
            "event_type": "checkout.session.completed",
            "payment_reference": "checkout_123abc",
            "status": "success",
            "amount": 10000,
            "raw": {"checkout_status": "complete"},
        }

        result = handle_wave_webhook(webhook_data)

        assert result is not None
        assert result.status == PaymentStatus.SUCCESS
        assert result.completed_at is not None

    def test_handle_webhook_expired(self, wave_payment):
        """Test handling expired payment webhook."""
        webhook_data = {
            "event_type": "checkout.session.expired",
            "payment_reference": "checkout_123abc",
            "status": "expired",
            "raw": {},
        }

        result = handle_wave_webhook(webhook_data)

        assert result is not None
        assert result.status == PaymentStatus.EXPIRED
        assert result.completed_at is not None

    def test_handle_webhook_failed(self, wave_payment):
        """Test handling failed payment webhook."""
        webhook_data = {
            "event_type": "checkout.session.failed",
            "payment_reference": "checkout_123abc",
            "status": "failed",
            "raw": {
                "error_code": "INSUFFICIENT_FUNDS",
                "error_message": "User has insufficient funds",
            },
        }

        result = handle_wave_webhook(webhook_data)

        assert result is not None
        assert result.status == PaymentStatus.FAILED
        # Error details from raw response
        assert "INSUFFICIENT_FUNDS" in result.error_code

    def test_handle_webhook_idempotent(self, wave_payment):
        """Test that webhook handler is idempotent."""
        webhook_data = {
            "event_type": "checkout.session.completed",
            "payment_reference": "checkout_123abc",
            "status": "success",
            "raw": {},
        }

        # First call
        result1 = handle_wave_webhook(webhook_data)
        assert result1.status == PaymentStatus.SUCCESS

        # Second call - should not fail, just return existing payment
        result2 = handle_wave_webhook(webhook_data)
        assert result2.status == PaymentStatus.SUCCESS
        assert result2.id == result1.id

    def test_handle_webhook_payment_not_found(self):
        """Test webhook handling when payment not found."""
        webhook_data = {
            "event_type": "checkout.session.completed",
            "payment_reference": "nonexistent_checkout",
            "status": "success",
            "raw": {},
        }

        result = handle_wave_webhook(webhook_data)

        assert result is None

    def test_handle_webhook_missing_reference(self):
        """Test webhook handling with missing reference."""
        webhook_data = {
            "event_type": "checkout.session.completed",
            "payment_reference": "",
            "status": "success",
            "raw": {},
        }

        result = handle_wave_webhook(webhook_data)

        assert result is None

    def test_handle_webhook_from_pending_state(self, owner):
        """Test webhook handling transitions payment from PENDING through PROCESSING to SUCCESS."""
        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="wave",
        )
        payment = PaymentFactory(
            business=owner.business,
            payment_method=payment_method,
            provider_code="wave",
            provider_reference="checkout_pending123",
            amount=10000,
        )
        # Payment is in PENDING state

        webhook_data = {
            "event_type": "checkout.session.completed",
            "payment_reference": "checkout_pending123",
            "status": "success",
            "raw": {},
        }

        result = handle_wave_webhook(webhook_data)

        assert result is not None
        assert result.status == PaymentStatus.SUCCESS


@pytest.mark.django_db
class TestWebhookTask:
    """Tests for Celery webhook processing task."""

    @pytest.fixture
    def wave_payment_for_task(self, owner):
        """Create a Wave payment for task testing."""
        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="wave",
            name="Wave",
        )
        payment = PaymentFactory(
            business=owner.business,
            payment_method=payment_method,
            provider_code="wave",
            provider_reference="checkout_task123",
            amount=10000,
        )
        payment.start_processing()
        payment.save()
        return payment

    def test_process_webhook_event_success(self, wave_payment_for_task):
        """Test async webhook processing task."""
        from apps.payments.tasks import process_webhook_event

        # Create valid webhook payload
        payload = {
            "type": "checkout.session.completed",
            "data": {
                "id": "checkout_task123",
                "amount": 10000,
                "currency": "XOF",
            },
        }
        body = json.dumps(payload)

        # Mock signature verification
        with patch("apps.payments.providers.wave.WaveProvider.verify_webhook") as mock_verify:
            mock_verify.return_value = True

            result = process_webhook_event(
                provider_code="wave",
                headers={"Wave-Signature": "t=123,v1=abc"},
                body=body,
            )

            assert result["success"] is True
            assert "payment_id" in result

    def test_process_webhook_event_invalid_signature(self, wave_payment_for_task):
        """Test webhook processing with invalid signature."""
        from apps.payments.tasks import process_webhook_event

        payload = {
            "type": "checkout.session.completed",
            "data": {"id": "checkout_task123"},
        }
        body = json.dumps(payload)

        with patch("apps.payments.providers.wave.WaveProvider.verify_webhook") as mock_verify:
            mock_verify.return_value = False

            result = process_webhook_event(
                provider_code="wave",
                headers={"Wave-Signature": "invalid"},
                body=body,
            )

            assert result["success"] is False
            assert "Invalid signature" in result["error"]

    def test_process_webhook_event_unknown_provider(self):
        """Test webhook processing with unknown provider."""
        from apps.payments.tasks import process_webhook_event

        result = process_webhook_event(
            provider_code="unknown_provider",
            headers={},
            body="{}",
        )

        assert result["success"] is False
        assert "Unknown payment provider" in result["error"]
