"""Paystack payment provider."""

import hashlib
import hmac
import json
import logging
from typing import Optional

import requests
from django.conf import settings

from .base import PaymentProvider, PaymentResult, ProviderStatus, RefundResult

logger = logging.getLogger(__name__)


class PaystackProvider(PaymentProvider):
    """
    Payment provider for Paystack card payments.

    Paystack is a Stripe-acquired payment provider popular in Africa.
    This provider creates payment links and handles webhook verification.
    """

    def __init__(self):
        """Initialize Paystack provider with settings."""
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.public_key = settings.PAYSTACK_PUBLIC_KEY
        self.api_url = settings.PAYSTACK_API_URL
        self._timeout = 30

    @property
    def provider_code(self) -> str:
        """Return the provider code."""
        return "paystack"

    def _get_headers(self) -> dict:
        """Get headers for Paystack API requests."""
        return {
            "Authorization": f"Bearer {self.secret_key}",
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
        Initiate a payment with Paystack.

        Creates a transaction and returns authorization URL.
        Note: Paystack expects amount in kobo (smallest currency unit).
        """
        url = f"{self.api_url}/transaction/initialize"

        # Paystack expects amount in smallest currency unit (kobo for NGN, pesewas for GHS)
        # XOF is already in smallest unit
        payload = {
            "amount": amount,  # Amount in smallest unit
            "email": f"{order_reference}@resto360.app",
            "currency": currency,
            "reference": idempotency_key,
            "callback_url": success_url,
            "metadata": {
                "order_reference": order_reference,
                "custom_fields": [
                    {
                        "display_name": "Order Reference",
                        "variable_name": "order_reference",
                        "value": order_reference,
                    }
                ],
            },
        }

        if customer_phone:
            payload["metadata"]["phone"] = customer_phone

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self._timeout,
            )

            if response.status_code in (200, 201):
                data = response.json()
                if data.get("status"):
                    return PaymentResult(
                        provider_reference=data.get("data", {}).get("reference", idempotency_key),
                        status=ProviderStatus.PENDING,
                        redirect_url=data.get("data", {}).get("authorization_url"),
                        raw_response=data,
                    )
                else:
                    return PaymentResult(
                        provider_reference="",
                        status=ProviderStatus.FAILED,
                        error_code="api_error",
                        error_message=data.get("message", "Unknown error"),
                        raw_response=data,
                    )
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except json.JSONDecodeError:
                    error_data = {"message": response.text}

                logger.error(
                    "Paystack transaction initialization failed: %s %s",
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
            logger.error("Paystack API request failed: %s", str(e))
            return PaymentResult(
                provider_reference="",
                status=ProviderStatus.FAILED,
                error_code="network_error",
                error_message=str(e),
                raw_response={"error": str(e)},
            )

    def check_status(self, provider_reference: str) -> PaymentResult:
        """
        Check the status of a Paystack payment.

        Args:
            provider_reference: The transaction reference from Paystack

        Returns:
            PaymentResult with current status
        """
        url = f"{self.api_url}/transaction/verify/{provider_reference}"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status"):
                    tx_data = data.get("data", {})
                    paystack_status = tx_data.get("status", "")

                    # Map Paystack status to our ProviderStatus
                    status_map = {
                        "success": ProviderStatus.SUCCESS,
                        "pending": ProviderStatus.PENDING,
                        "failed": ProviderStatus.FAILED,
                        "abandoned": ProviderStatus.EXPIRED,
                    }
                    status = status_map.get(paystack_status, ProviderStatus.PENDING)

                    return PaymentResult(
                        provider_reference=provider_reference,
                        status=status,
                        raw_response=data,
                    )

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
            logger.error("Paystack status check failed: %s", str(e))
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
        Process a refund for a Paystack payment.

        Args:
            provider_reference: The transaction reference from Paystack
            amount: Optional partial refund amount (full refund if not specified)

        Returns:
            RefundResult indicating success or failure
        """
        url = f"{self.api_url}/refund"

        payload = {
            "transaction": provider_reference,
        }
        if amount is not None:
            payload["amount"] = amount

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self._timeout,
            )

            if response.status_code in (200, 201):
                data = response.json()
                if data.get("status"):
                    return RefundResult(
                        success=True,
                        provider_reference=str(data.get("data", {}).get("id", provider_reference)),
                    )
                else:
                    return RefundResult(
                        success=False,
                        error_message=data.get("message", "Refund failed"),
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
            logger.error("Paystack refund request failed: %s", str(e))
            return RefundResult(
                success=False,
                error_message=str(e),
            )

    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """
        Verify the authenticity of a Paystack webhook request.

        Paystack uses HMAC-SHA512 signature verification.
        The signature is in the 'x-paystack-signature' header.

        Args:
            headers: Request headers containing signature
            body: Raw request body

        Returns:
            True if the webhook is authentic, False otherwise
        """
        if not self.secret_key:
            logger.warning("Paystack secret key not configured")
            return False

        # Get signature header (case-insensitive)
        signature = None
        for key, value in headers.items():
            if key.lower() == "x-paystack-signature":
                signature = value
                break

        if not signature:
            logger.warning("x-paystack-signature header missing")
            return False

        # Compute expected signature using HMAC-SHA512
        if isinstance(body, str):
            body = body.encode("utf-8")

        expected_signature = hmac.new(
            key=self.secret_key.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha512,
        ).hexdigest()

        # Compare signatures (constant-time comparison)
        if not hmac.compare_digest(expected_signature, signature):
            logger.warning("Paystack webhook signature mismatch")
            return False

        return True

    def parse_webhook(self, body: bytes) -> dict:
        """
        Parse a Paystack webhook request body.

        Returns normalized dict with:
        - event_type: Type of event (charge.success, etc.)
        - payment_reference: The transaction reference
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

        # Paystack webhook structure
        event_type = data.get("event", "")
        tx_data = data.get("data", {})

        # Map Paystack event types to normalized status
        status_map = {
            "charge.success": "success",
            "charge.failed": "failed",
            "transfer.success": "success",
            "transfer.failed": "failed",
        }

        return {
            "event_type": event_type,
            "payment_reference": tx_data.get("reference", ""),
            "status": status_map.get(event_type, "unknown"),
            "amount": int(tx_data.get("amount", 0)),
            "currency": tx_data.get("currency", "XOF"),
            "raw": data,
        }
