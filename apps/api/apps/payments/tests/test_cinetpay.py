"""Tests for CinetPay payment provider."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from apps.payments.providers.base import PaymentResult, ProviderStatus, RefundResult
from apps.payments.providers.cinetpay import CinetPayProvider


@pytest.fixture
def cinetpay_provider():
    """Create a CinetPay provider instance with test settings."""
    with patch.object(CinetPayProvider, "__init__", lambda self: None):
        provider = CinetPayProvider()
        provider.api_key = "test_api_key"
        provider.site_id = "test_site_id"
        provider.secret_key = "test_secret_key"
        provider.api_url = "https://api-checkout.cinetpay.com/v2"
        provider._timeout = 30
        return provider


@pytest.fixture
def mock_payment_response():
    """Mock successful payment creation response."""
    return {
        "code": "201",
        "message": "CREATED",
        "data": {
            "payment_url": "https://checkout.cinetpay.com/payment/xxx",
            "payment_token": "xxx",
        },
    }


@pytest.fixture
def mock_check_response():
    """Mock payment check response."""
    return {
        "code": "00",
        "message": "SUCCES",
        "data": {
            "amount": "10000",
            "currency": "XOF",
            "status": "ACCEPTED",
            "payment_method": "CREDIT_CARD",
        },
    }


class TestCinetPayProviderCode:
    """Tests for CinetPay provider code property."""

    def test_provider_code_is_cinetpay(self, cinetpay_provider):
        """Test that provider code is 'cinetpay'."""
        assert cinetpay_provider.provider_code == "cinetpay"


class TestCinetPayInitiatePayment:
    """Tests for CinetPay payment initiation."""

    def test_initiate_payment_success(self, cinetpay_provider, mock_payment_response):
        """Test successful payment initiation."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_payment_response
            mock_post.return_value = mock_response

            result = cinetpay_provider.initiate_payment(
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
            assert result.redirect_url == "https://checkout.cinetpay.com/payment/xxx"

            # Verify API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "payment" in call_args[0][0]
            payload = call_args[1]["json"]
            assert payload["amount"] == 10000
            assert payload["currency"] == "XOF"
            assert payload["transaction_id"] == "idem_123"
            assert payload["apikey"] == "test_api_key"
            assert payload["site_id"] == "test_site_id"

    def test_initiate_payment_includes_phone(self, cinetpay_provider, mock_payment_response):
        """Test that customer phone is included in payload."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_payment_response
            mock_post.return_value = mock_response

            cinetpay_provider.initiate_payment(
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
            assert payload["customer_phone_number"] == "+2250701234567"

    def test_initiate_payment_api_error(self, cinetpay_provider):
        """Test payment initiation with API error response."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "code": "601",
                "message": "INVALID_AMOUNT",
            }
            mock_post.return_value = mock_response

            result = cinetpay_provider.initiate_payment(
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
            assert result.error_code == "601"
            assert result.error_message == "INVALID_AMOUNT"

    def test_initiate_payment_network_error(self, cinetpay_provider):
        """Test payment initiation with network error."""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("Connection refused")

            result = cinetpay_provider.initiate_payment(
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


class TestCinetPayCheckStatus:
    """Tests for CinetPay status checking."""

    def test_check_status_accepted(self, cinetpay_provider, mock_check_response):
        """Test checking status of accepted payment."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_check_response
            mock_post.return_value = mock_response

            result = cinetpay_provider.check_status("idem_123")

            assert result.status == ProviderStatus.SUCCESS
            assert result.provider_reference == "idem_123"

            # Verify it uses POST with body
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["transaction_id"] == "idem_123"
            assert payload["apikey"] == "test_api_key"
            assert payload["site_id"] == "test_site_id"

    def test_check_status_pending(self, cinetpay_provider):
        """Test checking status of pending payment."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "code": "00",
                "data": {
                    "status": "PENDING",
                },
            }
            mock_post.return_value = mock_response

            result = cinetpay_provider.check_status("idem_123")

            assert result.status == ProviderStatus.PENDING

    def test_check_status_refused(self, cinetpay_provider):
        """Test checking status of refused payment."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "code": "00",
                "data": {
                    "status": "REFUSED",
                },
            }
            mock_post.return_value = mock_response

            result = cinetpay_provider.check_status("idem_123")

            assert result.status == ProviderStatus.FAILED

    def test_check_status_cancelled(self, cinetpay_provider):
        """Test checking status of cancelled payment."""
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "code": "00",
                "data": {
                    "status": "CANCELLED",
                },
            }
            mock_post.return_value = mock_response

            result = cinetpay_provider.check_status("idem_123")

            assert result.status == ProviderStatus.EXPIRED

    def test_check_status_network_error(self, cinetpay_provider):
        """Test status check with network error."""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("Timeout")

            result = cinetpay_provider.check_status("idem_123")

            assert result.status == ProviderStatus.PENDING
            assert result.error_code == "network_error"


class TestCinetPayRefund:
    """Tests for CinetPay refund processing."""

    def test_process_refund_not_supported(self, cinetpay_provider):
        """Test that refund returns manual processing required message."""
        result = cinetpay_provider.process_refund("idem_123")

        assert isinstance(result, RefundResult)
        assert result.success is False
        assert "manually" in result.error_message.lower()

    def test_process_refund_partial_not_supported(self, cinetpay_provider):
        """Test that partial refund also returns manual processing required."""
        result = cinetpay_provider.process_refund("idem_123", amount=5000)

        assert result.success is False
        assert "manually" in result.error_message.lower()


class TestCinetPayVerifyWebhook:
    """Tests for CinetPay webhook verification."""

    def test_verify_webhook_valid(self, cinetpay_provider):
        """Test webhook verification via API check."""
        body = b'{"cpm_trans_id": "idem_123"}'

        with patch.object(cinetpay_provider, "check_status") as mock_check:
            mock_check.return_value = PaymentResult(
                provider_reference="idem_123",
                status=ProviderStatus.SUCCESS,
                raw_response={"code": "00"},
            )

            result = cinetpay_provider.verify_webhook({}, body)

            assert result is True
            mock_check.assert_called_once_with("idem_123")

    def test_verify_webhook_invalid(self, cinetpay_provider):
        """Test webhook verification when API check fails."""
        body = b'{"cpm_trans_id": "idem_123"}'

        with patch.object(cinetpay_provider, "check_status") as mock_check:
            mock_check.return_value = PaymentResult(
                provider_reference="idem_123",
                status=ProviderStatus.PENDING,
                raw_response={"code": "404"},
            )

            result = cinetpay_provider.verify_webhook({}, body)

            assert result is False

    def test_verify_webhook_missing_transaction_id(self, cinetpay_provider):
        """Test webhook verification with missing transaction_id."""
        body = b'{"some_other_field": "value"}'

        result = cinetpay_provider.verify_webhook({}, body)

        assert result is False

    def test_verify_webhook_invalid_json(self, cinetpay_provider):
        """Test webhook verification with invalid JSON."""
        body = b"not valid json"

        result = cinetpay_provider.verify_webhook({}, body)

        assert result is False


class TestCinetPayParseWebhook:
    """Tests for CinetPay webhook parsing."""

    def test_parse_webhook_success(self, cinetpay_provider):
        """Test parsing successful payment webhook."""
        payload = {
            "cpm_trans_id": "idem_123",
            "cpm_result": "00",
            "cpm_amount": "10000",
            "cpm_currency": "XOF",
            "cpm_site_id": "test_site_id",
        }
        body = json.dumps(payload).encode("utf-8")

        result = cinetpay_provider.parse_webhook(body)

        assert result["event_type"] == "payment.notification"
        assert result["payment_reference"] == "idem_123"
        assert result["status"] == "success"
        assert result["amount"] == 10000

    def test_parse_webhook_failed(self, cinetpay_provider):
        """Test parsing failed payment webhook."""
        payload = {
            "cpm_trans_id": "idem_123",
            "cpm_result": "601",
            "cpm_amount": "10000",
            "cpm_currency": "XOF",
        }
        body = json.dumps(payload).encode("utf-8")

        result = cinetpay_provider.parse_webhook(body)

        assert result["status"] == "failed"

    def test_parse_webhook_invalid_json(self, cinetpay_provider):
        """Test parsing invalid JSON webhook."""
        body = b"not valid json"

        result = cinetpay_provider.parse_webhook(body)

        assert "error" in result
