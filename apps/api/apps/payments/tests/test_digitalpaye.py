"""Tests for DigitalPaye payment provider."""

import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from apps.payments.providers.base import ProviderStatus
from apps.payments.providers.digitalpaye import (
    DigitalPayeMTNProvider,
    DigitalPayeOrangeProvider,
    DigitalPayeProvider,
    DigitalPayeWaveProvider,
)


@pytest.fixture
def digitalpaye_settings():
    """Override settings for DigitalPaye tests."""
    return {
        "DIGITALPAYE_API_KEY": "test_api_key",
        "DIGITALPAYE_API_SECRET": "test_api_secret",
        "DIGITALPAYE_WEBHOOK_SECRET": "test_webhook_secret",
        "DIGITALPAYE_API_URL": "https://api.digitalpaye.com/v1",
        "DIGITALPAYE_ENVIRONMENT": "sandbox",
    }


@pytest.fixture
def wave_provider(digitalpaye_settings):
    """Create DigitalPaye Wave provider instance."""
    with override_settings(**digitalpaye_settings):
        return DigitalPayeWaveProvider()


@pytest.fixture
def orange_provider(digitalpaye_settings):
    """Create DigitalPaye Orange provider instance."""
    with override_settings(**digitalpaye_settings):
        return DigitalPayeOrangeProvider()


@pytest.fixture
def mtn_provider(digitalpaye_settings):
    """Create DigitalPaye MTN provider instance."""
    with override_settings(**digitalpaye_settings):
        return DigitalPayeMTNProvider()


class TestDigitalPayeProviderCodes:
    """Test provider code identification."""

    def test_wave_provider_code(self, wave_provider):
        """Test Wave provider code."""
        assert wave_provider.provider_code == "digitalpaye_wave"

    def test_orange_provider_code(self, orange_provider):
        """Test Orange provider code."""
        assert orange_provider.provider_code == "digitalpaye_orange"

    def test_mtn_provider_code(self, mtn_provider):
        """Test MTN provider code."""
        assert mtn_provider.provider_code == "digitalpaye_mtn"


class TestDigitalPayeInitiatePayment:
    """Test payment initiation."""

    @patch("apps.payments.providers.digitalpaye.requests.post")
    def test_initiate_payment_success(self, mock_post, wave_provider):
        """Test successful payment initiation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "transactionId": "txn_123456",
            "status": "PENDING",
            "paymentUrl": "https://pay.digitalpaye.com/checkout/abc123",
        }
        mock_post.return_value = mock_response

        result = wave_provider.initiate_payment(
            amount=5000,
            currency="XOF",
            order_reference="ORDER-001",
            customer_phone="+2250700000000",
            idempotency_key="idem_123",
            callback_url="https://example.com/webhook",
            success_url="https://example.com/success",
            error_url="https://example.com/error",
        )

        assert result.status == ProviderStatus.PENDING
        assert result.provider_reference == "txn_123456"
        assert result.redirect_url == "https://pay.digitalpaye.com/checkout/abc123"

    @patch("apps.payments.providers.digitalpaye.requests.post")
    def test_initiate_payment_immediate_success(self, mock_post, wave_provider):
        """Test payment that succeeds immediately."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transactionId": "txn_123456",
            "status": "SUCCESSFUL",
        }
        mock_post.return_value = mock_response

        result = wave_provider.initiate_payment(
            amount=5000,
            currency="XOF",
            order_reference="ORDER-001",
            customer_phone="+2250700000000",
            idempotency_key="idem_123",
            callback_url="https://example.com/webhook",
            success_url="https://example.com/success",
            error_url="https://example.com/error",
        )

        assert result.status == ProviderStatus.SUCCESS

    @patch("apps.payments.providers.digitalpaye.requests.post")
    def test_initiate_payment_duplicate_transaction(self, mock_post, wave_provider):
        """Test handling duplicate transaction error."""
        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.json.return_value = {
            "message": "Duplicate transaction ID",
        }
        mock_post.return_value = mock_response

        result = wave_provider.initiate_payment(
            amount=5000,
            currency="XOF",
            order_reference="ORDER-001",
            customer_phone="+2250700000000",
            idempotency_key="idem_duplicate",
            callback_url="https://example.com/webhook",
            success_url="https://example.com/success",
            error_url="https://example.com/error",
        )

        assert result.status == ProviderStatus.FAILED
        assert result.error_code == "409"
        assert "Duplicate transaction" in result.error_message

    @patch("apps.payments.providers.digitalpaye.requests.post")
    def test_initiate_payment_insufficient_funds(self, mock_post, wave_provider):
        """Test handling insufficient funds error."""
        mock_response = MagicMock()
        mock_response.status_code = 412
        mock_response.json.return_value = {
            "message": "Insufficient balance",
        }
        mock_post.return_value = mock_response

        result = wave_provider.initiate_payment(
            amount=5000,
            currency="XOF",
            order_reference="ORDER-001",
            customer_phone="+2250700000000",
            idempotency_key="idem_123",
            callback_url="https://example.com/webhook",
            success_url="https://example.com/success",
            error_url="https://example.com/error",
        )

        assert result.status == ProviderStatus.FAILED
        assert "Insufficient funds" in result.error_message


class TestDigitalPayeCheckStatus:
    """Test status checking."""

    @patch("apps.payments.providers.digitalpaye.requests.get")
    def test_check_status_successful(self, mock_get, wave_provider):
        """Test checking successful payment status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transactionId": "txn_123456",
            "status": "SUCCESSFUL",
            "amount": 5000,
            "currency": "XOF",
        }
        mock_get.return_value = mock_response

        result = wave_provider.check_status("txn_123456")

        assert result.status == ProviderStatus.SUCCESS
        assert result.provider_reference == "txn_123456"

    @patch("apps.payments.providers.digitalpaye.requests.get")
    def test_check_status_pending(self, mock_get, wave_provider):
        """Test checking pending payment status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transactionId": "txn_123456",
            "status": "PENDING",
        }
        mock_get.return_value = mock_response

        result = wave_provider.check_status("txn_123456")

        assert result.status == ProviderStatus.PENDING

    @patch("apps.payments.providers.digitalpaye.requests.get")
    def test_check_status_failed(self, mock_get, wave_provider):
        """Test checking failed payment status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transactionId": "txn_123456",
            "status": "FAILED",
        }
        mock_get.return_value = mock_response

        result = wave_provider.check_status("txn_123456")

        assert result.status == ProviderStatus.FAILED


class TestDigitalPayeWebhook:
    """Test webhook parsing."""

    def test_parse_webhook_success(self, wave_provider):
        """Test parsing successful payment webhook."""
        webhook_body = json.dumps({
            "event": "payment.completed",
            "transactionId": "txn_123456",
            "status": "SUCCESSFUL",
            "amount": 5000,
            "currency": "XOF",
            "operator": "WAVE_MONEY_CI",
            "customer": {
                "phone": "+2250700000000",
            },
        }).encode("utf-8")

        result = wave_provider.parse_webhook(webhook_body)

        assert result["status"] == "success"
        assert result["payment_reference"] == "txn_123456"
        assert result["amount"] == 5000
        assert result["currency"] == "XOF"

    def test_parse_webhook_failed(self, wave_provider):
        """Test parsing failed payment webhook."""
        webhook_body = json.dumps({
            "event": "payment.failed",
            "transactionId": "txn_123456",
            "status": "FAILED",
            "amount": 5000,
        }).encode("utf-8")

        result = wave_provider.parse_webhook(webhook_body)

        assert result["status"] == "failed"

    def test_parse_webhook_invalid_json(self, wave_provider):
        """Test parsing invalid JSON webhook."""
        webhook_body = b"invalid json"

        result = wave_provider.parse_webhook(webhook_body)

        assert "error" in result


class TestDigitalPayeOperators:
    """Test different operator configurations."""

    def test_wave_operator_code(self, wave_provider):
        """Test Wave operator code is set correctly."""
        assert wave_provider._operator_code == "WAVE_MONEY_CI"

    def test_orange_operator_code(self, orange_provider):
        """Test Orange operator code is set correctly."""
        assert orange_provider._operator_code == "ORANGE_MONEY_CI"

    def test_mtn_operator_code(self, mtn_provider):
        """Test MTN operator code is set correctly."""
        assert mtn_provider._operator_code == "MTN_MONEY_CI"


class TestDigitalPayeGetBalance:
    """Test balance inquiry."""

    @patch("apps.payments.providers.digitalpaye.requests.get")
    def test_get_balance_success(self, mock_get, wave_provider):
        """Test successful balance inquiry."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "amount": 1000000,
                "currency": "XOF",
            },
        }
        mock_get.return_value = mock_response

        result = wave_provider.get_balance()

        assert result["success"] is True
        assert result["balance"] == 1000000
        assert result["currency"] == "XOF"

    @patch("apps.payments.providers.digitalpaye.requests.get")
    def test_get_balance_failure(self, mock_get, wave_provider):
        """Test failed balance inquiry."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        result = wave_provider.get_balance()

        assert result["success"] is False


class TestProviderRegistry:
    """Test that DigitalPaye providers are registered."""

    def test_get_digitalpaye_wave_provider(self, digitalpaye_settings):
        """Test getting DigitalPaye Wave provider from registry."""
        from apps.payments.providers import get_provider

        with override_settings(**digitalpaye_settings):
            provider = get_provider("digitalpaye_wave")
            assert provider.provider_code == "digitalpaye_wave"

    def test_get_digitalpaye_orange_provider(self, digitalpaye_settings):
        """Test getting DigitalPaye Orange provider from registry."""
        from apps.payments.providers import get_provider

        with override_settings(**digitalpaye_settings):
            provider = get_provider("digitalpaye_orange")
            assert provider.provider_code == "digitalpaye_orange"

    def test_get_digitalpaye_mtn_provider(self, digitalpaye_settings):
        """Test getting DigitalPaye MTN provider from registry."""
        from apps.payments.providers import get_provider

        with override_settings(**digitalpaye_settings):
            provider = get_provider("digitalpaye_mtn")
            assert provider.provider_code == "digitalpaye_mtn"

    def test_get_digitalpaye_default_provider(self, digitalpaye_settings):
        """Test getting default DigitalPaye provider (Wave) from registry."""
        from apps.payments.providers import get_provider

        with override_settings(**digitalpaye_settings):
            provider = get_provider("digitalpaye")
            assert provider.provider_code == "digitalpaye_wave"
