"""DigitalPaye payment provider for West Africa.

DigitalPaye is a unified payment API supporting:
- Wave Money
- Orange Money
- MTN Mobile Money

Documentation: https://docs.digitalpaye.com
"""

import hashlib
import hmac
import json
import logging
from typing import Optional

import requests
from django.conf import settings

from .base import PaymentProvider, PaymentResult, ProviderStatus, RefundResult

logger = logging.getLogger(__name__)


class DigitalPayeProvider(PaymentProvider):
    """
    Payment provider for DigitalPaye unified mobile money API.

    DigitalPaye provides a single API to collect payments via Wave,
    Orange Money, and MTN Mobile Money in West Africa (Ivory Coast, Senegal, etc.).
    """

    # Supported operators (for reference)
    OPERATORS = {
        "wave": "WAVE_MONEY_CI",
        "orange": "ORANGE_MONEY_CI",
        "mtn": "MTN_MONEY_CI",
    }

    def __init__(self, operator: str = "wave"):
        """
        Initialize DigitalPaye provider with settings.

        Args:
            operator: The mobile money operator to use (wave, orange, mtn)
        """
        self.api_key = settings.DIGITALPAYE_API_KEY
        self.api_secret = settings.DIGITALPAYE_API_SECRET
        self.webhook_secret = settings.DIGITALPAYE_WEBHOOK_SECRET
        self.api_url = settings.DIGITALPAYE_API_URL
        self.environment = settings.DIGITALPAYE_ENVIRONMENT
        self._timeout = 30
        self._operator = operator
        self._operator_code = self.OPERATORS.get(operator, "WAVE_MONEY_CI")

    @property
    def provider_code(self) -> str:
        """Return the provider code."""
        return f"digitalpaye_{self._operator}"

    def _get_headers(self) -> dict:
        """Get headers for DigitalPaye API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Environment": "Production" if self.environment == "production" else "Sandbox",
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
        Initiate a payment with DigitalPaye.

        Creates a payment request using the DigitalPaye API.

        Args:
            amount: Payment amount in smallest currency unit (XOF integer)
            currency: Currency code (e.g., 'XOF')
            order_reference: Reference to the order being paid
            customer_phone: Customer phone number for mobile money
            idempotency_key: Unique key to prevent duplicate payments
            callback_url: URL for webhook notifications
            success_url: URL to redirect after successful payment
            error_url: URL to redirect after failed payment

        Returns:
            PaymentResult with provider reference and status
        """
        url = f"{self.api_url}/payment"

        # Build payload according to DigitalPaye API
        payload = {
            "transactionId": idempotency_key,
            "amount": amount,
            "currency": currency,
            "operator": self._operator_code,
            "customer": {
                "phone": customer_phone,
            },
            "payer": {
                "phone": customer_phone,
            },
            "recipient": {
                "phone": customer_phone,
            },
            "description": f"Payment for order {order_reference}",
            "callbackUrl": callback_url,
            "successUrl": success_url,
            "errorUrl": error_url,
            "metadata": {
                "order_reference": order_reference,
                "idempotency_key": idempotency_key,
            },
        }

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self._timeout,
            )

            data = {}
            try:
                data = response.json()
            except json.JSONDecodeError:
                data = {"message": response.text}

            if response.status_code in (200, 201, 202):
                # Map DigitalPaye status codes
                # 200 = SUCCESSFUL, 201 = CREATED, 202 = PAYMENT_IS_PENDING
                status = ProviderStatus.PENDING
                if response.status_code == 200 and data.get("status") == "SUCCESSFUL":
                    status = ProviderStatus.SUCCESS

                return PaymentResult(
                    provider_reference=data.get("transactionId", idempotency_key),
                    status=status,
                    redirect_url=data.get("paymentUrl"),
                    raw_response=data,
                )
            else:
                # Handle error responses
                error_code = str(response.status_code)
                error_message = self._get_error_message(response.status_code, data)

                logger.error(
                    "DigitalPaye payment creation failed: %s %s",
                    response.status_code,
                    error_message,
                )

                return PaymentResult(
                    provider_reference="",
                    status=ProviderStatus.FAILED,
                    error_code=error_code,
                    error_message=error_message,
                    raw_response=data,
                )

        except requests.RequestException as e:
            logger.error("DigitalPaye API request failed: %s", str(e))
            return PaymentResult(
                provider_reference="",
                status=ProviderStatus.FAILED,
                error_code="network_error",
                error_message=str(e),
                raw_response={"error": str(e)},
            )

    def _get_error_message(self, status_code: int, data: dict) -> str:
        """Map DigitalPaye error codes to human-readable messages."""
        error_messages = {
            400: "Missing required field",
            401: "Expired or invalid token",
            409: "Duplicate transaction",
            410: "Unsupported operator",
            412: "Insufficient funds",
            504: "Payment failed - timeout",
        }
        default_message = data.get("message", data.get("error", "Unknown error"))
        return error_messages.get(status_code, default_message)

    def check_status(self, provider_reference: str) -> PaymentResult:
        """
        Check the status of a DigitalPaye payment.

        Args:
            provider_reference: The transaction ID from DigitalPaye

        Returns:
            PaymentResult with current status
        """
        url = f"{self.api_url}/payment/{provider_reference}/status"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                dp_status = data.get("status", "").upper()

                # Map DigitalPaye status to our ProviderStatus
                status_map = {
                    "SUCCESSFUL": ProviderStatus.SUCCESS,
                    "SUCCESS": ProviderStatus.SUCCESS,
                    "PENDING": ProviderStatus.PENDING,
                    "PAYMENT_IS_PENDING": ProviderStatus.PENDING,
                    "PROCESSING": ProviderStatus.PROCESSING,
                    "FAILED": ProviderStatus.FAILED,
                    "EXPIRED": ProviderStatus.EXPIRED,
                    "CANCELLED": ProviderStatus.FAILED,
                }
                status = status_map.get(dp_status, ProviderStatus.PENDING)

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
            logger.error("DigitalPaye status check failed: %s", str(e))
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
        Process a refund/transfer for a DigitalPaye payment.

        Note: DigitalPaye uses the transfer endpoint for refunds.

        Args:
            provider_reference: The transaction ID from the original payment
            amount: Optional partial refund amount (full refund if not specified)

        Returns:
            RefundResult indicating success or failure
        """
        # First, get the original payment details
        status_result = self.check_status(provider_reference)
        if status_result.status != ProviderStatus.SUCCESS:
            return RefundResult(
                success=False,
                error_message="Cannot refund a payment that is not successful",
            )

        url = f"{self.api_url}/transfer"

        # Get customer phone from original payment
        original_data = status_result.raw_response or {}
        customer_phone = original_data.get("customer", {}).get("phone", "")
        original_amount = original_data.get("amount", 0)

        refund_amount = amount if amount is not None else original_amount

        payload = {
            "transactionId": f"refund_{provider_reference}",
            "amount": refund_amount,
            "currency": original_data.get("currency", "XOF"),
            "operator": self._operator_code,
            "recipient": {
                "phone": customer_phone,
            },
            "description": f"Refund for transaction {provider_reference}",
        }

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self._timeout,
            )

            if response.status_code in (200, 201, 202):
                data = response.json()
                return RefundResult(
                    success=True,
                    provider_reference=data.get("transactionId", f"refund_{provider_reference}"),
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
            logger.error("DigitalPaye refund request failed: %s", str(e))
            return RefundResult(
                success=False,
                error_message=str(e),
            )

    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """
        Verify the authenticity of a DigitalPaye webhook request.

        Args:
            headers: Request headers containing signature
            body: Raw request body

        Returns:
            True if the webhook is authentic, False otherwise
        """
        from ..webhooks.verification import verify_digitalpaye_signature

        return verify_digitalpaye_signature(
            headers=headers,
            body=body,
            secret=self.webhook_secret,
        )

    def parse_webhook(self, body: bytes) -> dict:
        """
        Parse a DigitalPaye webhook request body.

        Returns normalized dict with:
        - event_type: Type of event
        - payment_reference: The transaction ID
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

        # DigitalPaye webhook structure
        event_type = data.get("event", data.get("type", ""))
        dp_status = data.get("status", "").upper()

        # Map DigitalPaye status to normalized status
        status_map = {
            "SUCCESSFUL": "success",
            "SUCCESS": "success",
            "PENDING": "pending",
            "PAYMENT_IS_PENDING": "pending",
            "FAILED": "failed",
            "EXPIRED": "expired",
            "CANCELLED": "failed",
        }

        return {
            "event_type": event_type,
            "payment_reference": data.get("transactionId", data.get("data", {}).get("transactionId", "")),
            "status": status_map.get(dp_status, "unknown"),
            "amount": int(data.get("amount", data.get("data", {}).get("amount", 0))),
            "currency": data.get("currency", data.get("data", {}).get("currency", "XOF")),
            "operator": data.get("operator", data.get("data", {}).get("operator", "")),
            "customer_phone": data.get("customer", {}).get("phone", data.get("data", {}).get("customer", {}).get("phone", "")),
            "raw": data,
        }

    def get_balance(self) -> dict:
        """
        Get account balance from DigitalPaye.

        Returns:
            dict with balance information
        """
        url = f"{self.api_url}/balance"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "balance": data.get("data", {}).get("amount", 0),
                    "currency": data.get("data", {}).get("currency", "XOF"),
                    "raw": data,
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
            }


# Convenience classes for specific operators
class DigitalPayeWaveProvider(DigitalPayeProvider):
    """DigitalPaye provider for Wave Money."""

    def __init__(self):
        super().__init__(operator="wave")

    @property
    def provider_code(self) -> str:
        return "digitalpaye_wave"


class DigitalPayeOrangeProvider(DigitalPayeProvider):
    """DigitalPaye provider for Orange Money."""

    def __init__(self):
        super().__init__(operator="orange")

    @property
    def provider_code(self) -> str:
        return "digitalpaye_orange"


class DigitalPayeMTNProvider(DigitalPayeProvider):
    """DigitalPaye provider for MTN Mobile Money."""

    def __init__(self):
        super().__init__(operator="mtn")

    @property
    def provider_code(self) -> str:
        return "digitalpaye_mtn"
