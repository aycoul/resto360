"""Tests for Flutterwave payment provider."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from apps.payments.providers.base import PaymentResult, ProviderStatus, RefundResult
from apps.payments.providers.flutterwave import FlutterwaveProvider


@pytest.fixture
def flutterwave_provider():
    """Create a Flutterwave provider instance with test settings."""
    with patch.object(FlutterwaveProvider, "__init__", lambda self: None):
        provider = FlutterwaveProvider()
        provider.secret_key = "FLWSECK_TEST-xxx"
        provider.public_key = "FLWPUBK_TEST-xxx"
        provider.webhook_secret = "test_webhook_secret"
        provider.api_url = "https://api.flutterwave.com/v3"
        provider._timeout = 30
        return provider


@pytest.fixture
def mock_payment_response():
    """Mock successful payment creation response."""
    return {
        "status": "success",
        "message": "Hosted Link",
        "data": {
            "link": "https://checkout.flutterwave.com/v3/hosted/pay/xxx",
        },
    }


@pytest.fixture
def mock_verify_response():
    """Mock transaction verification response."""
    return {
        "status": "success",
        "message": "Transaction fetched successfully",
        "data": {
            "id": 123456789,
            "tx_ref": "idem_123",
            "amount": 10000,
            "currency": "XOF",
            "status": "successful",
        },
    }


class TestFlutterwaveProviderCode:
    """Tests for Flutterwave provider code property."""

    def test_provider_code_is_flutterwave(self, flutterwave_provider):
        """Test that provider code is 'flutterwave'."""
        assert flutterwave_provider.provider_code == "flutterwave"


class TestFlutterwaveInitiatePayment:
    """Tests for Flutterwave payment initiation."""

    def test_initiate_payment_success(self, flutterwave_provider, mock_payment_response):
        """Test successful payment initiation."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_payment_response
            mock_post.return_value = mock_response

            result = flutterwave_provider.initiate_payment(
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
            assert result.redirect_url == "https://checkout.flutterwave.com/v3/hosted/pay/xxx"

            # Verify API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "payments" in call_args[0][0]
            payload = call_args[1]["json"]
            assert payload["amount"] == 10000
            assert payload["currency"] == "XOF"
            assert payload["tx_ref"] == "idem_123"

    def test_initiate_payment_includes_customer_phone(
        self, flutterwave_provider, mock_payment_response
    ):
        """Test that customer phone is included in payload."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_payment_response
            mock_post.return_value = mock_response

            flutterwave_provider.initiate_payment(
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
            assert payload["customer"]["phonenumber"] == "+2250701234567"

    def test_initiate_payment_api_error(self, flutterwave_provider):
        """Test payment initiation with API error response."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"message": "Invalid amount"}
            mock_post.return_value = mock_response

            result = flutterwave_provider.initiate_payment(
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

    def test_initiate_payment_network_error(self, flutterwave_provider):
        """Test payment initiation with network error."""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("Connection refused")

            result = flutterwave_provider.initiate_payment(
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


class TestFlutterwaveCheckStatus:
    """Tests for Flutterwave status checking."""

    def test_check_status_successful(self, flutterwave_provider, mock_verify_response):
        """Test checking status of successful payment."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_verify_response
            mock_get.return_value = mock_response

            result = flutterwave_provider.check_status("idem_123")

            assert result.status == ProviderStatus.SUCCESS
            assert result.provider_reference == "123456789"

    def test_check_status_pending(self, flutterwave_provider):
        """Test checking status of pending payment."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "data": {
                    "id": 123456789,
                    "tx_ref": "idem_123",
                    "status": "pending",
                },
            }
            mock_get.return_value = mock_response

            result = flutterwave_provider.check_status("idem_123")

            assert result.status == ProviderStatus.PENDING

    def test_check_status_failed(self, flutterwave_provider):
        """Test checking status of failed payment."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "data": {
                    "id": 123456789,
                    "tx_ref": "idem_123",
                    "status": "failed",
                },
            }
            mock_get.return_value = mock_response

            result = flutterwave_provider.check_status("idem_123")

            assert result.status == ProviderStatus.FAILED

    def test_check_status_network_error(self, flutterwave_provider):
        """Test status check with network error."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Timeout")

            result = flutterwave_provider.check_status("idem_123")

            assert result.status == ProviderStatus.PENDING
            assert result.error_code == "network_error"


class TestFlutterwaveRefund:
    """Tests for Flutterwave refund processing."""

    def test_process_refund_full(self, flutterwave_provider):
        """Test processing a full refund."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "message": "Refund initiated",
                "data": {"id": 789},
            }
            mock_post.return_value = mock_response

            result = flutterwave_provider.process_refund("123456789")

            assert isinstance(result, RefundResult)
            assert result.success is True
            assert result.provider_reference == "789"

    def test_process_refund_partial(self, flutterwave_provider):
        """Test processing a partial refund."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "message": "Refund initiated",
                "data": {"id": 789},
            }
            mock_post.return_value = mock_response

            result = flutterwave_provider.process_refund("123456789", amount=5000)

            assert result.success is True

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["amount"] == 5000

    def test_process_refund_error(self, flutterwave_provider):
        """Test refund with API error."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"message": "Refund not allowed"}
            mock_post.return_value = mock_response

            result = flutterwave_provider.process_refund("123456789")

            assert result.success is False
            assert result.error_message == "Refund not allowed"


class TestFlutterwaveVerifyWebhook:
    """Tests for Flutterwave webhook verification."""

    def test_verify_webhook_valid(self, flutterwave_provider):
        """Test webhook verification with valid signature."""
        headers = {"verif-hash": "test_webhook_secret"}
        body = b'{"event": "charge.completed"}'

        result = flutterwave_provider.verify_webhook(headers, body)

        assert result is True

    def test_verify_webhook_invalid(self, flutterwave_provider):
        """Test webhook verification with invalid signature."""
        headers = {"verif-hash": "wrong_secret"}
        body = b'{"event": "charge.completed"}'

        result = flutterwave_provider.verify_webhook(headers, body)

        assert result is False

    def test_verify_webhook_missing_header(self, flutterwave_provider):
        """Test webhook verification with missing header."""
        headers = {}
        body = b'{"event": "charge.completed"}'

        result = flutterwave_provider.verify_webhook(headers, body)

        assert result is False


class TestFlutterwaveParseWebhook:
    """Tests for Flutterwave webhook parsing."""

    def test_parse_webhook_charge_completed(self, flutterwave_provider):
        """Test parsing charge.completed webhook."""
        payload = {
            "event": "charge.completed",
            "data": {
                "id": 123456789,
                "tx_ref": "idem_123",
                "amount": 10000,
                "currency": "XOF",
                "status": "successful",
            },
        }
        body = json.dumps(payload).encode("utf-8")

        result = flutterwave_provider.parse_webhook(body)

        assert result["event_type"] == "charge.completed"
        assert result["payment_reference"] == "idem_123"
        assert result["transaction_id"] == "123456789"
        assert result["status"] == "success"
        assert result["amount"] == 10000

    def test_parse_webhook_charge_failed(self, flutterwave_provider):
        """Test parsing charge.failed webhook."""
        payload = {
            "event": "charge.failed",
            "data": {
                "id": 123456789,
                "tx_ref": "idem_123",
                "amount": 10000,
                "status": "failed",
            },
        }
        body = json.dumps(payload).encode("utf-8")

        result = flutterwave_provider.parse_webhook(body)

        assert result["status"] == "failed"

    def test_parse_webhook_invalid_json(self, flutterwave_provider):
        """Test parsing invalid JSON webhook."""
        body = b"not valid json"

        result = flutterwave_provider.parse_webhook(body)

        assert "error" in result
