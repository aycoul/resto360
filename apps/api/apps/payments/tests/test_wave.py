"""Tests for Wave payment provider."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from apps.payments.providers.base import ProviderStatus, PaymentResult, RefundResult
from apps.payments.providers.wave import WaveProvider


@pytest.fixture
def wave_provider():
    """Create a Wave provider instance with test settings."""
    with patch.object(WaveProvider, '__init__', lambda self: None):
        provider = WaveProvider()
        provider.api_key = "test_api_key"
        provider.webhook_secret = "test_webhook_secret"
        provider.api_url = "https://api.wave.com/v1"
        provider._timeout = 30
        return provider


@pytest.fixture
def mock_checkout_response():
    """Mock successful checkout session creation response."""
    return {
        "id": "checkout_123abc",
        "amount": "10000",
        "currency": "XOF",
        "client_reference": "order_456",
        "checkout_status": "pending",
        "wave_launch_url": "https://pay.wave.com/checkout/123abc",
        "success_url": "https://example.com/success",
        "error_url": "https://example.com/error",
    }


@pytest.fixture
def mock_status_response():
    """Mock checkout session status response."""
    return {
        "id": "checkout_123abc",
        "amount": "10000",
        "currency": "XOF",
        "checkout_status": "complete",
        "client_reference": "order_456",
    }


class TestWaveProviderCode:
    """Tests for Wave provider code property."""

    def test_provider_code_is_wave(self, wave_provider):
        """Test that provider code is 'wave'."""
        assert wave_provider.provider_code == "wave"


class TestWaveInitiatePayment:
    """Tests for Wave payment initiation."""

    def test_initiate_payment_success(self, wave_provider, mock_checkout_response):
        """Test successful payment initiation."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = mock_checkout_response
            mock_post.return_value = mock_response

            result = wave_provider.initiate_payment(
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
            assert result.provider_reference == "checkout_123abc"
            assert result.status == ProviderStatus.PENDING
            assert result.redirect_url == "https://pay.wave.com/checkout/123abc"

            # Verify API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "checkout/sessions" in call_args[0][0]
            payload = call_args[1]["json"]
            assert payload["amount"] == "10000"  # String, not int
            assert payload["currency"] == "XOF"
            assert payload["client_reference"] == "order_456"

    def test_initiate_payment_includes_phone_restriction(self, wave_provider, mock_checkout_response):
        """Test that customer phone is included as restriction."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = mock_checkout_response
            mock_post.return_value = mock_response

            wave_provider.initiate_payment(
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
            assert payload["restrict_payer_mobile"] == "+2250701234567"

    def test_initiate_payment_without_phone(self, wave_provider, mock_checkout_response):
        """Test payment initiation without phone restriction."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = mock_checkout_response
            mock_post.return_value = mock_response

            wave_provider.initiate_payment(
                amount=10000,
                currency="XOF",
                order_reference="order_456",
                customer_phone="",
                idempotency_key="idem_123",
                callback_url="https://example.com/webhook",
                success_url="https://example.com/success",
                error_url="https://example.com/error",
            )

            payload = mock_post.call_args[1]["json"]
            assert "restrict_payer_mobile" not in payload

    def test_initiate_payment_api_error(self, wave_provider):
        """Test payment initiation with API error response."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"message": "Invalid amount"}
            mock_post.return_value = mock_response

            result = wave_provider.initiate_payment(
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

    def test_initiate_payment_network_error(self, wave_provider):
        """Test payment initiation with network error."""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("Connection refused")

            result = wave_provider.initiate_payment(
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


class TestWaveCheckStatus:
    """Tests for Wave status checking."""

    def test_check_status_complete(self, wave_provider, mock_status_response):
        """Test checking status of completed payment."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_status_response
            mock_get.return_value = mock_response

            result = wave_provider.check_status("checkout_123abc")

            assert result.status == ProviderStatus.SUCCESS
            assert result.provider_reference == "checkout_123abc"

    def test_check_status_pending(self, wave_provider):
        """Test checking status of pending payment."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "checkout_123abc",
                "checkout_status": "pending",
            }
            mock_get.return_value = mock_response

            result = wave_provider.check_status("checkout_123abc")

            assert result.status == ProviderStatus.PENDING

    def test_check_status_expired(self, wave_provider):
        """Test checking status of expired payment."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "checkout_123abc",
                "checkout_status": "expired",
            }
            mock_get.return_value = mock_response

            result = wave_provider.check_status("checkout_123abc")

            assert result.status == ProviderStatus.EXPIRED

    def test_check_status_network_error(self, wave_provider):
        """Test status check with network error."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Timeout")

            result = wave_provider.check_status("checkout_123abc")

            assert result.status == ProviderStatus.PENDING  # Fallback
            assert result.error_code == "network_error"


class TestWaveRefund:
    """Tests for Wave refund processing."""

    def test_process_refund_full(self, wave_provider):
        """Test processing a full refund."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "refund_789"}
            mock_post.return_value = mock_response

            result = wave_provider.process_refund("checkout_123abc")

            assert isinstance(result, RefundResult)
            assert result.success is True

            # Verify no amount in payload for full refund
            call_args = mock_post.call_args
            assert call_args[1].get("json") is None or "amount" not in call_args[1].get("json", {})

    def test_process_refund_partial(self, wave_provider):
        """Test processing a partial refund."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "refund_789"}
            mock_post.return_value = mock_response

            result = wave_provider.process_refund("checkout_123abc", amount=5000)

            assert result.success is True

            # Verify amount in payload as string
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["amount"] == "5000"

    def test_process_refund_error(self, wave_provider):
        """Test refund with API error."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"message": "Refund not allowed"}
            mock_post.return_value = mock_response

            result = wave_provider.process_refund("checkout_123abc")

            assert result.success is False
            assert result.error_message == "Refund not allowed"


class TestWaveParseWebhook:
    """Tests for Wave webhook parsing."""

    def test_parse_webhook_checkout_completed(self, wave_provider):
        """Test parsing checkout.session.completed webhook."""
        payload = {
            "type": "checkout.session.completed",
            "data": {
                "id": "checkout_123abc",
                "amount": 10000,
                "currency": "XOF",
                "client_reference": "order_456",
            },
        }
        body = json.dumps(payload).encode("utf-8")

        result = wave_provider.parse_webhook(body)

        assert result["event_type"] == "checkout.session.completed"
        assert result["payment_reference"] == "checkout_123abc"
        assert result["status"] == "success"
        assert result["amount"] == 10000
        assert result["client_reference"] == "order_456"

    def test_parse_webhook_checkout_expired(self, wave_provider):
        """Test parsing checkout.session.expired webhook."""
        payload = {
            "type": "checkout.session.expired",
            "data": {
                "id": "checkout_123abc",
                "amount": 10000,
            },
        }
        body = json.dumps(payload).encode("utf-8")

        result = wave_provider.parse_webhook(body)

        assert result["status"] == "expired"

    def test_parse_webhook_invalid_json(self, wave_provider):
        """Test parsing invalid JSON webhook."""
        body = b"not valid json"

        result = wave_provider.parse_webhook(body)

        assert "error" in result
