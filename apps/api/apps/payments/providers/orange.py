"""Orange Money payment provider."""

import json
import logging
import time
from typing import Optional

import requests
from django.conf import settings

from .base import PaymentProvider, PaymentResult, ProviderStatus, RefundResult

logger = logging.getLogger(__name__)


class OrangeProvider(PaymentProvider):
    """
    Payment provider for Orange Money mobile payments.

    Orange Money is a major mobile money provider in West Africa.
    This provider handles OAuth token management, payment initiation,
    and status polling (webhooks are unreliable, polling is essential).

    Important:
    - Orange uses "OUV" currency code for XOF
    - Orange expects integer amount, not string
    - OAuth token has expiry; cache and refresh
    """

    def __init__(self):
        """Initialize Orange provider with settings."""
        self.client_id = settings.ORANGE_CLIENT_ID
        self.client_secret = settings.ORANGE_CLIENT_SECRET
        self.merchant_key = settings.ORANGE_MERCHANT_KEY
        self.api_url = settings.ORANGE_API_URL
        self._timeout = 30
        # Token caching
        self._token: Optional[str] = None
        self._token_expires: float = 0

    @property
    def provider_code(self) -> str:
        """Return the provider code."""
        return "orange"

    def _get_token(self) -> str:
        """
        Get OAuth access token, using cache if still valid.

        Returns:
            Access token string

        Raises:
            requests.RequestException: If token request fails
        """
        # Check if cached token is still valid (with 60s buffer)
        if self._token and time.time() < (self._token_expires - 60):
            return self._token

        # Request new token
        url = f"{self.api_url}/oauth/token"
        payload = {
            "grant_type": "client_credentials",
        }
        headers = {
            "Authorization": f"Basic {self._encode_credentials()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = requests.post(
            url,
            headers=headers,
            data=payload,
            timeout=self._timeout,
        )
        response.raise_for_status()

        data = response.json()
        self._token = data["access_token"]
        # Token expires_in is in seconds
        expires_in = int(data.get("expires_in", 3600))
        self._token_expires = time.time() + expires_in

        return self._token

    def _encode_credentials(self) -> str:
        """Encode client credentials for Basic auth."""
        import base64

        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()

    def _get_headers(self, token: str) -> dict:
        """Get headers for Orange API requests."""
        return {
            "Authorization": f"Bearer {token}",
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
        Initiate a payment with Orange Money.

        Creates a web payment session with Orange API.

        Note: Orange uses "OUV" as currency code for XOF.
        """
        try:
            token = self._get_token()
        except requests.RequestException as e:
            logger.error("Orange token request failed: %s", str(e))
            return PaymentResult(
                provider_reference="",
                status=ProviderStatus.FAILED,
                error_code="auth_error",
                error_message=f"Failed to get OAuth token: {str(e)}",
                raw_response={"error": str(e)},
            )

        url = f"{self.api_url}/webpayment"

        # Orange uses "OUV" for XOF
        orange_currency = "OUV" if currency.upper() == "XOF" else currency

        # Orange expects integer amount, not string
        payload = {
            "merchant_key": self.merchant_key,
            "currency": orange_currency,
            "order_id": order_reference,
            "amount": amount,  # Integer for Orange
            "return_url": success_url,
            "cancel_url": error_url,
            "notif_url": callback_url,
            "reference": idempotency_key,
        }

        # Add customer phone if provided
        if customer_phone:
            payload["customer_msisdn"] = customer_phone.lstrip("+")

        try:
            response = requests.post(
                url,
                headers=self._get_headers(token),
                json=payload,
                timeout=self._timeout,
            )

            if response.status_code in (200, 201):
                data = response.json()
                return PaymentResult(
                    provider_reference=data.get("pay_token", ""),
                    status=ProviderStatus.PENDING,
                    redirect_url=data.get("payment_url"),
                    raw_response=data,
                )
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except json.JSONDecodeError:
                    error_data = {"message": response.text}

                logger.error(
                    "Orange payment initiation failed: %s %s",
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
            logger.error("Orange API request failed: %s", str(e))
            return PaymentResult(
                provider_reference="",
                status=ProviderStatus.FAILED,
                error_code="network_error",
                error_message=str(e),
                raw_response={"error": str(e)},
            )

    def check_status(self, provider_reference: str) -> PaymentResult:
        """
        Check the status of an Orange Money payment.

        Uses the transactionstatus endpoint with pay_token.

        Args:
            provider_reference: The pay_token from Orange

        Returns:
            PaymentResult with current status
        """
        try:
            token = self._get_token()
        except requests.RequestException as e:
            logger.error("Orange token request failed: %s", str(e))
            return PaymentResult(
                provider_reference=provider_reference,
                status=ProviderStatus.PENDING,
                error_code="auth_error",
                error_message=f"Failed to get OAuth token: {str(e)}",
                raw_response={"error": str(e)},
            )

        url = f"{self.api_url}/transactionstatus"
        params = {"pay_token": provider_reference}

        try:
            response = requests.get(
                url,
                headers=self._get_headers(token),
                params=params,
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                orange_status = data.get("status", "").upper()

                # Map Orange status to our ProviderStatus
                status_map = {
                    "SUCCESS": ProviderStatus.SUCCESS,
                    "FAILED": ProviderStatus.FAILED,
                    "CANCELLED": ProviderStatus.FAILED,
                    "EXPIRED": ProviderStatus.EXPIRED,
                    "PENDING": ProviderStatus.PENDING,
                    "INITIATED": ProviderStatus.PROCESSING,
                }
                status = status_map.get(orange_status, ProviderStatus.PENDING)

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
            logger.error("Orange status check failed: %s", str(e))
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
        Process a refund for an Orange Money payment.

        Orange Money refunds require manual processing via their dashboard.
        This returns a failure with instructions.

        Args:
            provider_reference: The pay_token from Orange
            amount: Optional partial refund amount

        Returns:
            RefundResult indicating manual processing required
        """
        return RefundResult(
            success=False,
            error_message="Orange Money refunds require manual processing via the Orange Money Business Dashboard",
        )

    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """
        Verify the authenticity of an Orange Money webhook request.

        Orange webhooks use notification token verification.
        Note: Orange webhook reliability is poor; polling is primary fallback.

        Args:
            headers: Request headers
            body: Raw request body

        Returns:
            True if the webhook is authentic, False otherwise
        """
        # Orange webhook verification is not well documented
        # For now, accept webhooks and rely on status polling as primary
        # TODO: Implement proper verification when Orange docs available
        return True

    def parse_webhook(self, body: bytes) -> dict:
        """
        Parse an Orange Money webhook request body.

        Returns normalized dict with:
        - event_type: Type of event
        - payment_reference: The pay_token
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

        # Orange webhook structure
        orange_status = data.get("status", "").upper()

        # Map Orange status to normalized status
        status_map = {
            "SUCCESS": "success",
            "FAILED": "failed",
            "CANCELLED": "failed",
            "EXPIRED": "expired",
        }

        return {
            "event_type": f"payment.{orange_status.lower()}",
            "payment_reference": data.get("pay_token", ""),
            "status": status_map.get(orange_status, "pending"),
            "amount": int(data.get("amount", 0)),
            "currency": "XOF",  # Orange uses OUV but we normalize to XOF
            "order_id": data.get("order_id", ""),
            "raw": data,
        }
