"""Tests for Paystack payment provider."""

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from apps.payments.providers.base import PaymentResult, ProviderStatus, RefundResult
from apps.payments.providers.paystack import PaystackProvider


@pytest.fixture
def paystack_provider():
    """Create a Paystack provider instance with test settings."""
    with patch.object(PaystackProvider, "__init__", lambda self: None):
        provider = PaystackProvider()
        provider.secret_key = "sk_test_xxx"
        provider.public_key = "pk_test_xxx"
        provider.api_url = "https://api.paystack.co"
        provider._timeout = 30
        return provider


@pytest.fixture
def mock_init_response():
    """Mock successful transaction initialization response."""
    return {
        "status": True,
        "message": "Authorization URL created",
        "data": {
            "authorization_url": "https://checkout.paystack.com/xxx",
            "access_code": "xxx",
            "reference": "idem_123",
        },
    }


@pytest.fixture
def mock_verify_response():
    """Mock transaction verification response."""
    return {
        "status": True,
        "message": "Verification successful",
        "data": {
            "id": 123456789,
            "reference": "idem_123",
            "amount": 10000,
            "currency": "XOF",
            "status": "success",
        },
    }


class TestPaystackProviderCode:
    """Tests for Paystack provider code property."""

    def test_provider_code_is_paystack(self, paystack_provider):
        """Test that provider code is 'paystack'."""
        assert paystack_provider.provider_code == "paystack"


class TestPaystackInitiatePayment:
    """Tests for Paystack payment initiation."""

    def test_initiate_payment_success(self, paystack_provider, mock_init_response):
        """Test successful payment initiation."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_init_response
            mock_post.return_value = mock_response

            result = paystack_provider.initiate_payment(
                amount=10000,
                currency="XOF",
                order_reference="order_456",
                customer_phone="+2250701234567",
                idempotency_key="idem_123",
                callback_url="https://example.com/webhook",
                success_url="https://example.com/success",
                error_url="https://example.com/error",
            )

            assert isinstance(result, PaymentResult)
            assert result.provider_reference == "idem_123"
            assert result.status == ProviderStatus.PENDING
            assert result.redirect_url == "https://checkout.paystack.com/xxx"

            # Verify API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "transaction/initialize" in call_args[0][0]
            payload = call_args[1]["json"]
            assert payload["amount"] == 10000
            assert payload["currency"] == "XOF"
            assert payload["reference"] == "idem_123"

    def test_initiate_payment_includes_metadata(self, paystack_provider, mock_init_response):
        """Test that metadata is included in payload."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_init_response
            mock_post.return_value = mock_response

            paystack_provider.initiate_payment(
                amount=10000,
                currency="XOF",
                order_reference="order_456",
                customer_phone="+2250701234567",
                idempotency_key="idem_123",
                callback_url="https://example.com/webhook",
                success_url="https://example.com/success",
                error_url="https://example.com/error",
            )

            payload = mock_post.call_args[1]["json"]
            assert payload["metadata"]["phone"] == "+2250701234567"
            assert payload["metadata"]["order_reference"] == "order_456"

    def test_initiate_payment_api_error(self, paystack_provider):
        """Test payment initiation with API error response."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"message": "Invalid amount"}
            mock_post.return_value = mock_response

            result = paystack_provider.initiate_payment(
                amount=10000,
                currency="XOF",
                order_reference="order_456",
                customer_phone="",
                idempotency_key="idem_123",
                callback_url="https://example.com/webhook",
                success_url="https://example.com/success",
                error_url="https://example.com/error",
            )

            assert result.status == ProviderStatus.FAILED
            assert result.error_code == "400"
            assert result.error_message == "Invalid amount"

    def test_initiate_payment_network_error(self, paystack_provider):
        """Test payment initiation with network error."""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("Connection refused")

            result = paystack_provider.initiate_payment(
                amount=10000,
                currency="XOF",
                order_reference="order_456",
                customer_phone="",
                idempotency_key="idem_123",
                callback_url="https://example.com/webhook",
                success_url="https://example.com/success",
                error_url="https://example.com/error",
            )

            assert result.status == ProviderStatus.FAILED
            assert result.error_code == "network_error"
            assert "Connection refused" in result.error_message


class TestPaystackCheckStatus:
    """Tests for Paystack status checking."""

    def test_check_status_success(self, paystack_provider, mock_verify_response):
        """Test checking status of successful payment."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_verify_response
            mock_get.return_value = mock_response

            result = paystack_provider.check_status("idem_123")

            assert result.status == ProviderStatus.SUCCESS
            assert result.provider_reference == "idem_123"

    def test_check_status_pending(self, paystack_provider):
        """Test checking status of pending payment."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": True,
                "data": {
                    "reference": "idem_123",
                    "status": "pending",
                },
            }
            mock_get.return_value = mock_response

            result = paystack_provider.check_status("idem_123")

            assert result.status == ProviderStatus.PENDING

    def test_check_status_abandoned(self, paystack_provider):
        """Test checking status of abandoned payment."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": True,
                "data": {
                    "reference": "idem_123",
                    "status": "abandoned",
                },
            }
            mock_get.return_value = mock_response

            result = paystack_provider.check_status("idem_123")

            assert result.status == ProviderStatus.EXPIRED

    def test_check_status_network_error(self, paystack_provider):
        """Test status check with network error."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Timeout")

            result = paystack_provider.check_status("idem_123")

            assert result.status == ProviderStatus.PENDING
            assert result.error_code == "network_error"


class TestPaystackRefund:
    """Tests for Paystack refund processing."""

    def test_process_refund_full(self, paystack_provider):
        """Test processing a full refund."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": True,
                "message": "Refund created",
                "data": {"id": 789},
            }
            mock_post.return_value = mock_response

            result = paystack_provider.process_refund("idem_123")

            assert isinstance(result, RefundResult)
            assert result.success is True
            assert result.provider_reference == "789"

            # Verify no amount in payload for full refund
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert "amount" not in payload

    def test_process_refund_partial(self, paystack_provider):
        """Test processing a partial refund."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": True,
                "message": "Refund created",
                "data": {"id": 789},
            }
            mock_post.return_value = mock_response

            result = paystack_provider.process_refund("idem_123", amount=5000)

            assert result.success is True

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["amount"] == 5000

    def test_process_refund_error(self, paystack_provider):
        """Test refund with API error."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"message": "Refund not allowed"}
            mock_post.return_value = mock_response

            result = paystack_provider.process_refund("idem_123")

            assert result.success is False
            assert result.error_message == "Refund not allowed"


class TestPaystackVerifyWebhook:
    """Tests for Paystack webhook verification."""

    def test_verify_webhook_valid(self, paystack_provider):
        """Test webhook verification with valid signature."""
        body = b'{"event": "charge.success"}'
        expected_signature = hmac.new(
            key=b"sk_test_xxx",
            msg=body,
            digestmod=hashlib.sha512,
        ).hexdigest()
        headers = {"x-paystack-signature": expected_signature}

        result = paystack_provider.verify_webhook(headers, body)

        assert result is True

    def test_verify_webhook_invalid(self, paystack_provider):
        """Test webhook verification with invalid signature."""
        headers = {"x-paystack-signature": "wrong_signature"}
        body = b'{"event": "charge.success"}'

        result = paystack_provider.verify_webhook(headers, body)

        assert result is False

    def test_verify_webhook_missing_header(self, paystack_provider):
        """Test webhook verification with missing header."""
        headers = {}
        body = b'{"event": "charge.success"}'

        result = paystack_provider.verify_webhook(headers, body)

        assert result is False


class TestPaystackParseWebhook:
    """Tests for Paystack webhook parsing."""

    def test_parse_webhook_charge_success(self, paystack_provider):
        """Test parsing charge.success webhook."""
        payload = {
            "event": "charge.success",
            "data": {
                "id": 123456789,
                "reference": "idem_123",
                "amount": 10000,
                "currency": "XOF",
                "status": "success",
            },
        }
        body = json.dumps(payload).encode("utf-8")

        result = paystack_provider.parse_webhook(body)

        assert result["event_type"] == "charge.success"
        assert result["payment_reference"] == "idem_123"
        assert result["status"] == "success"
        assert result["amount"] == 10000

    def test_parse_webhook_charge_failed(self, paystack_provider):
        """Test parsing charge.failed webhook."""
        payload = {
            "event": "charge.failed",
            "data": {
                "id": 123456789,
                "reference": "idem_123",
                "amount": 10000,
            },
        }
        body = json.dumps(payload).encode("utf-8")

        result = paystack_provider.parse_webhook(body)

        assert result["status"] == "failed"

    def test_parse_webhook_invalid_json(self, paystack_provider):
        """Test parsing invalid JSON webhook."""
        body = b"not valid json"

        result = paystack_provider.parse_webhook(body)

        assert "error" in result
