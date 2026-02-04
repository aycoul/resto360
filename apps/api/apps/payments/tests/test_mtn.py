"""Tests for MTN MoMo payment provider."""

import pytest
from unittest.mock import patch, MagicMock
import json

from apps.payments.providers.mtn import MTNProvider
from apps.payments.providers.base import ProviderStatus


@pytest.mark.django_db
class TestMTNProvider:
    """Tests for MTNProvider."""

    def test_mtn_provider_code(self):
        """Test that provider code is 'mtn'."""
        provider = MTNProvider()
        assert provider.provider_code == "mtn"

    def test_sandbox_uses_eur_currency(self):
        """Test that sandbox environment uses EUR currency."""
        with patch.object(MTNProvider, "__init__", lambda self: None):
            provider = MTNProvider()
            provider.environment = "sandbox"

            assert provider._get_currency() == "EUR"

    def test_production_uses_xof_currency(self):
        """Test that production environment uses XOF currency."""
        with patch.object(MTNProvider, "__init__", lambda self: None):
            provider = MTNProvider()
            provider.environment = "production"

            assert provider._get_currency() == "XOF"

    @patch("apps.payments.providers.mtn.requests.post")
    def test_initiate_payment_returns_202(self, mock_post):
        """Test that 202 Accepted is correctly handled."""
        # Mock token response
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test_token_123",
        }
        token_response.raise_for_status = MagicMock()

        # Mock payment initiation response (202 Accepted)
        payment_response = MagicMock()
        payment_response.status_code = 202  # MTN returns 202 Accepted

        # Configure mock to return different responses
        mock_post.side_effect = [token_response, payment_response]

        provider = MTNProvider()
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

        assert result.status == ProviderStatus.PENDING
        assert result.provider_reference  # Should have a UUID reference

    @patch("apps.payments.providers.mtn.requests.post")
    @patch("apps.payments.providers.mtn.requests.get")
    def test_check_status_success(self, mock_get, mock_post):
        """Test successful status check."""
        # Mock token response
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test_token_123",
        }
        token_response.raise_for_status = MagicMock()
        mock_post.return_value = token_response

        # Mock status check response
        status_response = MagicMock()
        status_response.status_code = 200
        status_response.json.return_value = {
            "status": "SUCCESSFUL",
            "amount": "10000",
            "currency": "EUR",
        }
        mock_get.return_value = status_response

        provider = MTNProvider()
        result = provider.check_status("test-reference-uuid")

        assert result.status == ProviderStatus.SUCCESS

    @patch("apps.payments.providers.mtn.requests.post")
    def test_phone_number_stripped(self, mock_post):
        """Test that + prefix is removed from phone numbers."""
        # Mock token response
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test_token_123",
        }
        token_response.raise_for_status = MagicMock()

        # Mock payment initiation response
        payment_response = MagicMock()
        payment_response.status_code = 202

        mock_post.side_effect = [token_response, payment_response]

        provider = MTNProvider()
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

        # Check that the second call (payment initiation) stripped the +
        payment_call = mock_post.call_args_list[1]
        payload = payment_call[1]["json"]
        assert payload["payer"]["partyId"] == "2250700000000"  # No + prefix

    def test_process_refund_not_supported(self):
        """Test that refunds return failure message."""
        provider = MTNProvider()
        result = provider.process_refund("mtn-reference-uuid")

        assert result.success is False
        assert "disbursement" in result.error_message.lower()

    def test_verify_webhook_returns_true(self):
        """Test that webhook verification returns True (not implemented)."""
        provider = MTNProvider()
        result = provider.verify_webhook({}, b'{"test": "data"}')

        # Currently returns True as fallback
        assert result is True

    def test_parse_webhook_success(self):
        """Test parsing of MTN webhook payload."""
        provider = MTNProvider()

        webhook_body = json.dumps({
            "status": "SUCCESSFUL",
            "referenceId": "mtn-ref-xyz",
            "externalId": "ORDER-456",
            "amount": "15000",
            "currency": "EUR",
        }).encode("utf-8")

        result = provider.parse_webhook(webhook_body)

        assert result["payment_reference"] == "mtn-ref-xyz"
        assert result["status"] == "success"
        assert result["amount"] == 15000

    def test_parse_webhook_failed_status(self):
        """Test parsing of failed MTN webhook."""
        provider = MTNProvider()

        webhook_body = json.dumps({
            "status": "FAILED",
            "referenceId": "mtn-ref-fail",
            "externalId": "ORDER-789",
            "amount": "5000",
            "reason": "Insufficient funds",
        }).encode("utf-8")

        result = provider.parse_webhook(webhook_body)

        assert result["status"] == "failed"

    def test_parse_webhook_pending_status(self):
        """Test parsing of pending MTN webhook."""
        provider = MTNProvider()

        webhook_body = json.dumps({
            "status": "PENDING",
            "referenceId": "mtn-ref-pending",
        }).encode("utf-8")

        result = provider.parse_webhook(webhook_body)

        assert result["status"] == "pending"

    def test_parse_webhook_invalid_json(self):
        """Test parsing of invalid JSON webhook."""
        provider = MTNProvider()

        result = provider.parse_webhook(b"not valid json")

        assert "error" in result

    @patch("apps.payments.providers.mtn.requests.post")
    def test_sandbox_does_not_send_callback_url(self, mock_post):
        """Test that sandbox environment does not send X-Callback-Url header."""
        # Mock token response
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test_token_123",
        }
        token_response.raise_for_status = MagicMock()

        # Mock payment initiation response
        payment_response = MagicMock()
        payment_response.status_code = 202

        mock_post.side_effect = [token_response, payment_response]

        provider = MTNProvider()
        provider.environment = "sandbox"
        provider.callback_url = "https://example.com/webhook"

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

        # Check that the second call (payment initiation) does not have X-Callback-Url
        payment_call = mock_post.call_args_list[1]
        headers = payment_call[1]["headers"]
        assert "X-Callback-Url" not in headers

    def test_sandbox_base_url(self):
        """Test that sandbox uses correct base URL."""
        provider = MTNProvider()
        # Default is sandbox
        assert "sandbox" in provider.base_url

    @patch("apps.payments.providers.mtn.requests.post")
    @patch("apps.payments.providers.mtn.requests.get")
    def test_check_status_failed(self, mock_get, mock_post):
        """Test failed status check."""
        # Mock token response
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test_token_123",
        }
        token_response.raise_for_status = MagicMock()
        mock_post.return_value = token_response

        # Mock status check response
        status_response = MagicMock()
        status_response.status_code = 200
        status_response.json.return_value = {
            "status": "FAILED",
            "reason": "Insufficient funds",
        }
        mock_get.return_value = status_response

        provider = MTNProvider()
        result = provider.check_status("test-reference-uuid")

        assert result.status == ProviderStatus.FAILED
