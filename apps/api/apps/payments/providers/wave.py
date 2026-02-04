"""Wave Money payment provider."""

import json
import logging
from typing import Optional

import requests
from django.conf import settings

from .base import PaymentProvider, PaymentResult, ProviderStatus, RefundResult

logger = logging.getLogger(__name__)


class WaveProvider(PaymentProvider):
    """
    Payment provider for Wave Money mobile payments.

    Wave is the most popular mobile money provider in Ivory Coast.
    This provider creates checkout sessions and handles webhook verification.
    """

    def __init__(self):
        """Initialize Wave provider with settings."""
        self.api_key = settings.WAVE_API_KEY
        self.webhook_secret = settings.WAVE_WEBHOOK_SECRET
        self.api_url = settings.WAVE_API_URL
        self._timeout = 30

    @property
    def provider_code(self) -> str:
        """Return the provider code."""
        return "wave"

    def _get_headers(self) -> dict:
        """Get headers for Wave API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def initiate_payment(
        self,
        amount: int,
        currency: str,
        order_reference: str,
        customer_phone: str,
        idempotency_key: str,
        callback_url: str,
        success_url: str,
        error_url: str,
    ) -> PaymentResult:
        """
        Initiate a payment with Wave Money.

        Creates a checkout session with Wave API.

        Note: Wave expects amount as a string, not integer.
        """
        url = f"{self.api_url}/checkout/sessions"

        # Wave expects amount as string
        payload = {
            "amount": str(amount),
            "currency": currency,
            "client_reference": order_reference,
            "success_url": success_url,
            "error_url": error_url,
        }

        # Optionally restrict to specific phone number
        if customer_phone:
            payload["restrict_payer_mobile"] = customer_phone

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self._timeout,
            )

            if response.status_code in (200, 201):
                data = response.json()
                return PaymentResult(
                    provider_reference=data.get("id", ""),
                    status=ProviderStatus.PENDING,
                    redirect_url=data.get("wave_launch_url"),
                    raw_response=data,
                )
            else:
                # Handle error response
                error_data = {}
                try:
                    error_data = response.json()
                except json.JSONDecodeError:
                    error_data = {"message": response.text}

                logger.error(
                    "Wave checkout session creation failed: %s %s",
                    response.status_code,
                    error_data,
                )

                return PaymentResult(
                    provider_reference="",
                    status=ProviderStatus.FAILED,
                    error_code=str(response.status_code),
                    error_message=error_data.get("message", "Unknown error"),
                    raw_response=error_data,
                )

        except requests.RequestException as e:
            logger.error("Wave API request failed: %s", str(e))
            return PaymentResult(
                provider_reference="",
                status=ProviderStatus.FAILED,
                error_code="network_error",
                error_message=str(e),
                raw_response={"error": str(e)},
            )

    def check_status(self, provider_reference: str) -> PaymentResult:
        """
        Check the status of a Wave payment.

        Args:
            provider_reference: The checkout session ID from Wave

        Returns:
            PaymentResult with current status
        """
        url = f"{self.api_url}/checkout/sessions/{provider_reference}"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                wave_status = data.get("checkout_status", "")

                # Map Wave status to our ProviderStatus
                status_map = {
                    "complete": ProviderStatus.SUCCESS,
                    "expired": ProviderStatus.EXPIRED,
                    "pending": ProviderStatus.PENDING,
                    "processing": ProviderStatus.PROCESSING,
                    "failed": ProviderStatus.FAILED,
                }
                status = status_map.get(wave_status, ProviderStatus.PENDING)

                return PaymentResult(
                    provider_reference=provider_reference,
                    status=status,
                    raw_response=data,
                )
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except json.JSONDecodeError:
                    error_data = {"message": response.text}

                return PaymentResult(
                    provider_reference=provider_reference,
                    status=ProviderStatus.PENDING,
                    error_code=str(response.status_code),
                    error_message=error_data.get("message", "Unknown error"),
                    raw_response=error_data,
                )

        except requests.RequestException as e:
            logger.error("Wave status check failed: %s", str(e))
            return PaymentResult(
                provider_reference=provider_reference,
                status=ProviderStatus.PENDING,
                error_code="network_error",
                error_message=str(e),
                raw_response={"error": str(e)},
            )

    def process_refund(
        self, provider_reference: str, amount: Optional[int] = None
    ) -> RefundResult:
        """
        Process a refund for a Wave payment.

        Args:
            provider_reference: The checkout session ID from Wave
            amount: Optional partial refund amount (full refund if not specified)

        Returns:
            RefundResult indicating success or failure
        """
        url = f"{self.api_url}/checkout/sessions/{provider_reference}/refund"

        payload = {}
        if amount is not None:
            # Wave expects amount as string
            payload["amount"] = str(amount)

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload if payload else None,
                timeout=self._timeout,
            )

            if response.status_code in (200, 201):
                data = response.json()
                return RefundResult(
                    success=True,
                    provider_reference=data.get("id", provider_reference),
                )
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except json.JSONDecodeError:
                    error_data = {"message": response.text}

                return RefundResult(
                    success=False,
                    error_message=error_data.get("message", "Refund failed"),
                )

        except requests.RequestException as e:
            logger.error("Wave refund request failed: %s", str(e))
            return RefundResult(
                success=False,
                error_message=str(e),
            )

    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """
        Verify the authenticity of a Wave webhook request.

        Wave uses HMAC-SHA256 signature verification with timestamp.
        Delegates to verification module for the actual verification.

        Args:
            headers: Request headers containing signature
            body: Raw request body

        Returns:
            True if the webhook is authentic, False otherwise
        """
        # Import here to avoid circular imports
        from ..webhooks.verification import verify_wave_signature

        return verify_wave_signature(
            headers=headers,
            body=body,
            secret=self.webhook_secret,
        )

    def parse_webhook(self, body: bytes) -> dict:
        """
        Parse a Wave webhook request body.

        Returns normalized dict with:
        - event_type: Type of event (checkout.session.completed, etc.)
        - payment_reference: The checkout session ID
        - status: Normalized status
        - amount: Payment amount
        - raw: Original payload

        Args:
            body: Raw request body

        Returns:
            Parsed webhook data as a dictionary
        """
        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"error": "Invalid JSON", "raw": body.decode("utf-8", errors="replace")}

        # Wave webhook structure
        event_type = data.get("type", "")
        checkout_data = data.get("data", {})

        # Map Wave event types to normalized status
        status_map = {
            "checkout.session.completed": "success",
            "checkout.session.expired": "expired",
            "checkout.session.failed": "failed",
        }

        return {
            "event_type": event_type,
            "payment_reference": checkout_data.get("id", ""),
            "status": status_map.get(event_type, "unknown"),
            "amount": int(checkout_data.get("amount", 0)),
            "currency": checkout_data.get("currency", "XOF"),
            "client_reference": checkout_data.get("client_reference", ""),
            "raw": data,
        }
