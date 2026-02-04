"""Tests for Orange Money payment provider."""

import pytest
from unittest.mock import patch, MagicMock
import json
import time

from apps.payments.providers.orange import OrangeProvider
from apps.payments.providers.base import ProviderStatus


@pytest.mark.django_db
class TestOrangeProvider:
    """Tests for OrangeProvider."""

    def test_orange_provider_code(self):
        """Test that provider code is 'orange'."""
        provider = OrangeProvider()
        assert provider.provider_code == "orange"

    @patch("apps.payments.providers.orange.requests.post")
    def test_initiate_payment_success(self, mock_post):
        """Test successful payment initiation with Orange Money."""
        # Mock token response
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test_token_123",
            "expires_in": 3600,
        }
        token_response.raise_for_status = MagicMock()

        # Mock payment initiation response
        payment_response = MagicMock()
        payment_response.status_code = 200
        payment_response.json.return_value = {
            "pay_token": "orange_pay_token_abc",
            "payment_url": "https://orange.com/pay/abc123",
        }

        # Configure mock to return different responses
        mock_post.side_effect = [token_response, payment_response]

        provider = OrangeProvider()
        result = provider.initiate_payment(
            amount=10000,
            currency="XOF",
            order_reference="ORDER-123",
            customer_phone="+2250700000000",
            idempotency_key="idem-123",
            callback_url="https://example.com/webhook",
            success_url="https://example.com/success",
            error_url="https://example.com/error",
        )

        assert result.provider_reference == "orange_pay_token_abc"
        assert result.status == ProviderStatus.PENDING
        assert result.redirect_url == "https://orange.com/pay/abc123"

    @patch("apps.payments.providers.orange.requests.post")
    @patch("apps.payments.providers.orange.requests.get")
    def test_check_status_success(self, mock_get, mock_post):
        """Test successful status check."""
        # Mock token response
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test_token_123",
            "expires_in": 3600,
        }
        token_response.raise_for_status = MagicMock()
        mock_post.return_value = token_response

        # Mock status check response
        status_response = MagicMock()
        status_response.status_code = 200
        status_response.json.return_value = {
            "status": "SUCCESS",
            "txnid": "orange_txn_123",
        }
        mock_get.return_value = status_response

        provider = OrangeProvider()
        result = provider.check_status("orange_pay_token_abc")

        assert result.provider_reference == "orange_pay_token_abc"
        assert result.status == ProviderStatus.SUCCESS

    @patch("apps.payments.providers.orange.requests.post")
    def test_token_caching(self, mock_post):
        """Test that OAuth token is cached and reused."""
        # Mock token response
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test_token_123",
            "expires_in": 3600,  # 1 hour
        }
        token_response.raise_for_status = MagicMock()
        mock_post.return_value = token_response

        provider = OrangeProvider()

        # First call should request token
        token1 = provider._get_token()
        assert token1 == "test_token_123"
        assert mock_post.call_count == 1

        # Second call should use cached token
        token2 = provider._get_token()
        assert token2 == "test_token_123"
        assert mock_post.call_count == 1  # Still 1, no new request

    def test_process_refund_not_supported(self):
        """Test that refunds return failure message."""
        provider = OrangeProvider()
        result = provider.process_refund("orange_pay_token_abc")

        assert result.success is False
        assert "manual processing" in result.error_message.lower()

    def test_verify_webhook_returns_true(self):
        """Test that webhook verification returns True (not implemented)."""
        provider = OrangeProvider()
        result = provider.verify_webhook({}, b'{"test": "data"}')

        # Currently returns True as fallback
        assert result is True

    def test_parse_webhook_success(self):
        """Test parsing of Orange webhook payload."""
        provider = OrangeProvider()

        webhook_body = json.dumps({
            "status": "SUCCESS",
            "pay_token": "orange_pay_token_xyz",
            "amount": 15000,
            "order_id": "ORDER-456",
        }).encode("utf-8")

        result = provider.parse_webhook(webhook_body)

        assert result["payment_reference"] == "orange_pay_token_xyz"
        assert result["status"] == "success"
        assert result["amount"] == 15000
        assert result["currency"] == "XOF"

    def test_parse_webhook_failed_status(self):
        """Test parsing of failed Orange webhook."""
        provider = OrangeProvider()

        webhook_body = json.dumps({
            "status": "FAILED",
            "pay_token": "orange_pay_token_fail",
            "amount": 5000,
        }).encode("utf-8")

        result = provider.parse_webhook(webhook_body)

        assert result["status"] == "failed"

    def test_parse_webhook_invalid_json(self):
        """Test parsing of invalid JSON webhook."""
        provider = OrangeProvider()

        result = provider.parse_webhook(b"not valid json")

        assert "error" in result

    @patch("apps.payments.providers.orange.requests.post")
    def test_initiate_payment_uses_ouv_currency(self, mock_post):
        """Test that Orange uses OUV currency code for XOF."""
        # Mock token response
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test_token_123",
            "expires_in": 3600,
        }
        token_response.raise_for_status = MagicMock()

        # Mock payment response
        payment_response = MagicMock()
        payment_response.status_code = 200
        payment_response.json.return_value = {
            "pay_token": "orange_token",
            "payment_url": "https://orange.com/pay",
        }

        mock_post.side_effect = [token_response, payment_response]

        provider = OrangeProvider()
        provider.initiate_payment(
            amount=10000,
            currency="XOF",
            order_reference="ORDER-123",
            customer_phone="+2250700000000",
            idempotency_key="idem-123",
            callback_url="https://example.com/webhook",
            success_url="https://example.com/success",
            error_url="https://example.com/error",
        )

        # Check that the second call (payment initiation) used OUV
        payment_call = mock_post.call_args_list[1]
        payload = payment_call[1]["json"]
        assert payload["currency"] == "OUV"
