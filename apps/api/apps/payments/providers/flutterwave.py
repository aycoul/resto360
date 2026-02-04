"""Flutterwave payment provider."""

import hashlib
import hmac
import json
import logging
from typing import Optional

import requests
from django.conf import settings

from .base import PaymentProvider, PaymentResult, ProviderStatus, RefundResult

logger = logging.getLogger(__name__)


class FlutterwaveProvider(PaymentProvider):
    """
    Payment provider for Flutterwave card payments.

    Flutterwave is a Pan-African payment provider supporting cards and mobile money.
    This provider creates payment links and handles webhook verification.
    """

    def __init__(self):
        """Initialize Flutterwave provider with settings."""
        self.secret_key = settings.FLUTTERWAVE_SECRET_KEY
        self.public_key = settings.FLUTTERWAVE_PUBLIC_KEY
        self.webhook_secret = settings.FLUTTERWAVE_WEBHOOK_SECRET
        self.api_url = settings.FLUTTERWAVE_API_URL
        self._timeout = 30

    @property
    def provider_code(self) -> str:
        """Return the provider code."""
        return "flutterwave"

    def _get_headers(self) -> dict:
        """Get headers for Flutterwave API requests."""
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
        Initiate a payment with Flutterwave.

        Creates a payment link with Flutterwave API.
        """
        url = f"{self.api_url}/payments"

        payload = {
            "tx_ref": idempotency_key,
            "amount": amount,
            "currency": currency,
            "redirect_url": success_url,
            "customer": {
                "email": f"{order_reference}@resto360.app",
                "phonenumber": customer_phone if customer_phone else None,
            },
            "customizations": {
                "title": "RESTO360 Payment",
                "description": f"Payment for order {order_reference}",
            },
            "meta": {
                "order_reference": order_reference,
            },
        }

        # Remove None values from customer
        payload["customer"] = {k: v for k, v in payload["customer"].items() if v is not None}

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self._timeout,
            )

            if response.status_code in (200, 201):
                data = response.json()
                if data.get("status") == "success":
                    return PaymentResult(
                        provider_reference=idempotency_key,
                        status=ProviderStatus.PENDING,
                        redirect_url=data.get("data", {}).get("link"),
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
                    "Flutterwave payment creation failed: %s %s",
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
            logger.error("Flutterwave API request failed: %s", str(e))
            return PaymentResult(
                provider_reference="",
                status=ProviderStatus.FAILED,
                error_code="network_error",
                error_message=str(e),
                raw_response={"error": str(e)},
            )

    def check_status(self, provider_reference: str) -> PaymentResult:
        """
        Check the status of a Flutterwave payment.

        Args:
            provider_reference: The transaction reference (tx_ref) from Flutterwave

        Returns:
            PaymentResult with current status
        """
        url = f"{self.api_url}/transactions/verify_by_reference"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params={"tx_ref": provider_reference},
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    tx_data = data.get("data", {})
                    flw_status = tx_data.get("status", "")

                    # Map Flutterwave status to our ProviderStatus
                    status_map = {
                        "successful": ProviderStatus.SUCCESS,
                        "pending": ProviderStatus.PENDING,
                        "failed": ProviderStatus.FAILED,
                    }
                    status = status_map.get(flw_status, ProviderStatus.PENDING)

                    return PaymentResult(
                        provider_reference=str(tx_data.get("id", provider_reference)),
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
            logger.error("Flutterwave status check failed: %s", str(e))
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
        Process a refund for a Flutterwave payment.

        Args:
            provider_reference: The transaction ID from Flutterwave
            amount: Optional partial refund amount (full refund if not specified)

        Returns:
            RefundResult indicating success or failure
        """
        url = f"{self.api_url}/transactions/{provider_reference}/refund"

        payload = {}
        if amount is not None:
            payload["amount"] = amount

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload if payload else None,
                timeout=self._timeout,
            )

            if response.status_code in (200, 201):
                data = response.json()
                if data.get("status") == "success":
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
            logger.error("Flutterwave refund request failed: %s", str(e))
            return RefundResult(
                success=False,
                error_message=str(e),
            )

    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """
        Verify the authenticity of a Flutterwave webhook request.

        Flutterwave uses HMAC-SHA256 signature verification.
        The signature is in the 'verif-hash' header.

        Args:
            headers: Request headers containing signature
            body: Raw request body

        Returns:
            True if the webhook is authentic, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("Flutterwave webhook secret not configured")
            return False

        # Get signature header (case-insensitive)
        signature = None
        for key, value in headers.items():
            if key.lower() == "verif-hash":
                signature = value
                break

        if not signature:
            logger.warning("verif-hash header missing")
            return False

        # Compare with our secret hash
        # Flutterwave sends the secret key hash directly
        if signature != self.webhook_secret:
            logger.warning("Flutterwave webhook signature mismatch")
            return False

        return True

    def parse_webhook(self, body: bytes) -> dict:
        """
        Parse a Flutterwave webhook request body.

        Returns normalized dict with:
        - event_type: Type of event (charge.completed, etc.)
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

        # Flutterwave webhook structure
        event_type = data.get("event", "")
        tx_data = data.get("data", {})

        # Map Flutterwave event types to normalized status
        status_map = {
            "charge.completed": "success",
            "charge.failed": "failed",
        }

        # Get transaction status for additional verification
        tx_status = tx_data.get("status", "")
        if tx_status == "successful":
            normalized_status = "success"
        elif tx_status == "failed":
            normalized_status = "failed"
        else:
            normalized_status = status_map.get(event_type, "unknown")

        return {
            "event_type": event_type,
            "payment_reference": tx_data.get("tx_ref", ""),
            "transaction_id": str(tx_data.get("id", "")),
            "status": normalized_status,
            "amount": int(tx_data.get("amount", 0)),
            "currency": tx_data.get("currency", "XOF"),
            "raw": data,
        }
