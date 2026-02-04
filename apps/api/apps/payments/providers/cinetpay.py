"""CinetPay payment provider."""

import json
import logging
from typing import Optional

import requests
from django.conf import settings

from .base import PaymentProvider, PaymentResult, ProviderStatus, RefundResult

logger = logging.getLogger(__name__)


class CinetPayProvider(PaymentProvider):
    """
    Payment provider for CinetPay card payments.

    CinetPay is an Abidjan-based payment provider focused on Francophone Africa.
    This provider creates payment links and handles webhook verification.
    """

    def __init__(self):
        """Initialize CinetPay provider with settings."""
        self.api_key = settings.CINETPAY_API_KEY
        self.site_id = settings.CINETPAY_SITE_ID
        self.secret_key = settings.CINETPAY_SECRET_KEY
        self.api_url = settings.CINETPAY_API_URL
        self._timeout = 30

    @property
    def provider_code(self) -> str:
        """Return the provider code."""
        return "cinetpay"

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
        Initiate a payment with CinetPay.

        Creates a payment link with CinetPay API.
        Note: CinetPay uses apikey in request body, not header.
        """
        url = f"{self.api_url}/payment"

        payload = {
            "apikey": self.api_key,
            "site_id": self.site_id,
            "transaction_id": idempotency_key,
            "amount": amount,
            "currency": currency,
            "description": f"Payment for order {order_reference}",
            "return_url": success_url,
            "notify_url": callback_url,
            "channels": "ALL",
            "metadata": order_reference,
        }

        if customer_phone:
            payload["customer_phone_number"] = customer_phone

        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=self._timeout,
            )

            if response.status_code in (200, 201):
                data = response.json()
                if data.get("code") == "201":
                    return PaymentResult(
                        provider_reference=idempotency_key,
                        status=ProviderStatus.PENDING,
                        redirect_url=data.get("data", {}).get("payment_url"),
                        raw_response=data,
                    )
                else:
                    return PaymentResult(
                        provider_reference="",
                        status=ProviderStatus.FAILED,
                        error_code=data.get("code", "unknown"),
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
                    "CinetPay payment creation failed: %s %s",
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
            logger.error("CinetPay API request failed: %s", str(e))
            return PaymentResult(
                provider_reference="",
                status=ProviderStatus.FAILED,
                error_code="network_error",
                error_message=str(e),
                raw_response={"error": str(e)},
            )

    def check_status(self, provider_reference: str) -> PaymentResult:
        """
        Check the status of a CinetPay payment.

        CinetPay uses POST with transaction_id in body to check status.

        Args:
            provider_reference: The transaction ID from CinetPay

        Returns:
            PaymentResult with current status
        """
        url = f"{self.api_url}/payment/check"

        payload = {
            "apikey": self.api_key,
            "site_id": self.site_id,
            "transaction_id": provider_reference,
        }

        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "00":
                    tx_data = data.get("data", {})
                    cinetpay_status = tx_data.get("status", "")

                    # Map CinetPay status to our ProviderStatus
                    status_map = {
                        "ACCEPTED": ProviderStatus.SUCCESS,
                        "PENDING": ProviderStatus.PENDING,
                        "REFUSED": ProviderStatus.FAILED,
                        "CANCELLED": ProviderStatus.EXPIRED,
                    }
                    status = status_map.get(cinetpay_status, ProviderStatus.PENDING)

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
                error_code=error_data.get("code", str(response.status_code)),
                error_message=error_data.get("message", "Unknown error"),
                raw_response=error_data,
            )

        except requests.RequestException as e:
            logger.error("CinetPay status check failed: %s", str(e))
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
        Process a refund for a CinetPay payment.

        Note: CinetPay does not support API-based refunds.
        Refunds must be processed manually through their dashboard.

        Args:
            provider_reference: The transaction ID from CinetPay
            amount: Optional partial refund amount (not supported)

        Returns:
            RefundResult indicating failure (manual process required)
        """
        logger.warning(
            "CinetPay refund requested for %s - manual processing required",
            provider_reference,
        )
        return RefundResult(
            success=False,
            error_message="CinetPay refunds must be processed manually through the dashboard",
        )

    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """
        Verify the authenticity of a CinetPay webhook request.

        CinetPay does not use signature verification for webhooks.
        Instead, we verify by calling the check API to confirm the transaction.

        Args:
            headers: Request headers (not used)
            body: Raw request body

        Returns:
            True if the transaction can be verified via API, False otherwise
        """
        if not self.api_key or not self.site_id:
            logger.warning("CinetPay credentials not configured")
            return False

        # Parse the body to get transaction_id
        try:
            data = json.loads(body.decode("utf-8"))
            transaction_id = data.get("cpm_trans_id") or data.get("transaction_id")
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Failed to parse CinetPay webhook body")
            return False

        if not transaction_id:
            logger.warning("No transaction_id in CinetPay webhook")
            return False

        # Verify by calling check API
        result = self.check_status(transaction_id)
        return result.raw_response is not None and result.raw_response.get("code") == "00"

    def parse_webhook(self, body: bytes) -> dict:
        """
        Parse a CinetPay webhook request body.

        Returns normalized dict with:
        - event_type: Type of event (payment notification)
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

        # CinetPay webhook structure
        # They send cpm_trans_id, cpm_site_id, cpm_amount, etc.
        status_code = data.get("cpm_result", "")

        # Map CinetPay result codes to normalized status
        # 00 = success, others = failed
        if status_code == "00":
            normalized_status = "success"
        else:
            normalized_status = "failed"

        return {
            "event_type": "payment.notification",
            "payment_reference": data.get("cpm_trans_id", ""),
            "status": normalized_status,
            "amount": int(data.get("cpm_amount", 0)),
            "currency": data.get("cpm_currency", "XOF"),
            "raw": data,
        }
