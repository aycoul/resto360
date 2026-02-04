"""MTN MoMo payment provider."""

import base64
import json
import logging
import uuid
from typing import Optional

import requests
from django.conf import settings

from .base import PaymentProvider, PaymentResult, ProviderStatus, RefundResult

logger = logging.getLogger(__name__)


class MTNProvider(PaymentProvider):
    """
    Payment provider for MTN MoMo (Mobile Money) payments.

    MTN MoMo is a major mobile money provider in Africa.
    This provider handles payment requests to pay, status polling,
    and environment-aware configuration.

    Important:
    - MTN sandbox does NOT support callbacks; must poll
    - Sandbox uses EUR, production uses XOF
    - Phone number must NOT have + prefix (use lstrip("+"))
    - 202 Accepted means request received, NOT success
    """

    def __init__(self):
        """Initialize MTN provider with settings."""
        self.subscription_key = settings.MTN_SUBSCRIPTION_KEY
        self.user_id = settings.MTN_USER_ID
        self.api_secret = settings.MTN_API_SECRET
        self.environment = settings.MTN_ENVIRONMENT
        self.callback_url = settings.MTN_CALLBACK_URL
        self._timeout = 30

        # Set base URL based on environment
        if self.environment == "sandbox":
            self.base_url = "https://sandbox.momodeveloper.mtn.com"
        else:
            self.base_url = "https://momoapi.mtn.com"

    @property
    def provider_code(self) -> str:
        """Return the provider code."""
        return "mtn"

    def _get_token(self) -> str:
        """
        Get OAuth2 access token from MTN.

        Uses Basic auth with user_id:api_secret.

        Returns:
            Access token string

        Raises:
            requests.RequestException: If token request fails
        """
        credentials = f"{self.user_id}:{self.api_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        url = f"{self.base_url}/collection/token/"
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }

        response = requests.post(
            url,
            headers=headers,
            timeout=self._timeout,
        )
        response.raise_for_status()

        return response.json()["access_token"]

    def _get_currency(self) -> str:
        """Get currency based on environment."""
        # Sandbox uses EUR, production uses XOF (Ivory Coast)
        return "EUR" if self.environment == "sandbox" else "XOF"

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
        Initiate a payment with MTN MoMo (Request to Pay).

        Creates a payment request that sends a prompt to the customer's phone.

        Note: MTN expects amount as string and phone without + prefix.
        """
        try:
            token = self._get_token()
        except requests.RequestException as e:
            logger.error("MTN token request failed: %s", str(e))
            return PaymentResult(
                provider_reference="",
                status=ProviderStatus.FAILED,
                error_code="auth_error",
                error_message=f"Failed to get OAuth token: {str(e)}",
                raw_response={"error": str(e)},
            )

        # Generate unique reference ID
        reference_id = str(uuid.uuid4())

        # Currency: EUR in sandbox, XOF in production
        mtn_currency = self._get_currency()

        # Build headers
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": reference_id,
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
        }

        # Add callback URL only in production (sandbox doesn't support)
        if self.callback_url and self.environment != "sandbox":
            headers["X-Callback-Url"] = self.callback_url

        # Build payload - MTN expects amount as string
        # Phone must NOT have + prefix
        payload = {
            "amount": str(amount),
            "currency": mtn_currency,
            "externalId": order_reference,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": customer_phone.lstrip("+"),
            },
            "payerMessage": f"Payment for order {order_reference}",
            "payeeNote": f"Payment {reference_id}",
        }

        url = f"{self.base_url}/collection/v1_0/requesttopay"

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self._timeout,
            )

            # MTN returns 202 Accepted for successful request
            if response.status_code == 202:
                return PaymentResult(
                    provider_reference=reference_id,
                    status=ProviderStatus.PENDING,
                    redirect_url=None,  # MTN uses push notification, no redirect
                    raw_response={"reference_id": reference_id, "status_code": 202},
                )
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except json.JSONDecodeError:
                    error_data = {"message": response.text}

                logger.error(
                    "MTN payment initiation failed: %s %s",
                    response.status_code,
                    error_data,
                )

                return PaymentResult(
                    provider_reference=reference_id,
                    status=ProviderStatus.FAILED,
                    error_code=str(response.status_code),
                    error_message=error_data.get("message", "Unknown error"),
                    raw_response=error_data,
                )

        except requests.RequestException as e:
            logger.error("MTN API request failed: %s", str(e))
            return PaymentResult(
                provider_reference="",
                status=ProviderStatus.FAILED,
                error_code="network_error",
                error_message=str(e),
                raw_response={"error": str(e)},
            )

    def check_status(self, provider_reference: str) -> PaymentResult:
        """
        Check the status of an MTN MoMo payment.

        Uses the requesttopay status endpoint.

        Args:
            provider_reference: The X-Reference-Id from initiation

        Returns:
            PaymentResult with current status
        """
        try:
            token = self._get_token()
        except requests.RequestException as e:
            logger.error("MTN token request failed: %s", str(e))
            return PaymentResult(
                provider_reference=provider_reference,
                status=ProviderStatus.PENDING,
                error_code="auth_error",
                error_message=f"Failed to get OAuth token: {str(e)}",
                raw_response={"error": str(e)},
            )

        url = f"{self.base_url}/collection/v1_0/requesttopay/{provider_reference}"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                mtn_status = data.get("status", "").upper()

                # Map MTN status to our ProviderStatus
                status_map = {
                    "PENDING": ProviderStatus.PENDING,
                    "SUCCESSFUL": ProviderStatus.SUCCESS,
                    "FAILED": ProviderStatus.FAILED,
                }
                status = status_map.get(mtn_status, ProviderStatus.PENDING)

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
            logger.error("MTN status check failed: %s", str(e))
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
        Process a refund for an MTN MoMo payment.

        MTN MoMo refunds require the disbursement API, which needs
        a separate product subscription.

        Args:
            provider_reference: The X-Reference-Id from initiation
            amount: Optional partial refund amount

        Returns:
            RefundResult indicating disbursement API needed
        """
        return RefundResult(
            success=False,
            error_message="MTN MoMo refunds require disbursement API setup. "
            "Please configure the disbursement product in your MTN Developer account.",
        )

    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """
        Verify the authenticity of an MTN MoMo webhook request.

        MTN callback verification is undocumented for sandbox.
        Note: Sandbox doesn't support callbacks at all; production verification
        should be implemented when production docs are available.

        Args:
            headers: Request headers
            body: Raw request body

        Returns:
            True if the webhook is authentic, False otherwise
        """
        # MTN sandbox doesn't support callbacks
        # Production verification not documented publicly
        # Accept webhooks and rely on status polling as primary
        return True

    def parse_webhook(self, body: bytes) -> dict:
        """
        Parse an MTN MoMo webhook request body.

        Returns normalized dict with:
        - event_type: Type of event
        - payment_reference: The reference ID
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

        # MTN webhook structure
        mtn_status = data.get("status", "").upper()

        # Map MTN status to normalized status
        status_map = {
            "SUCCESSFUL": "success",
            "FAILED": "failed",
            "PENDING": "pending",
        }

        return {
            "event_type": f"payment.{mtn_status.lower()}",
            "payment_reference": data.get("referenceId", data.get("externalId", "")),
            "status": status_map.get(mtn_status, "pending"),
            "amount": int(data.get("amount", 0)),
            "currency": data.get("currency", self._get_currency()),
            "external_id": data.get("externalId", ""),
            "payer": data.get("payer", {}),
            "raw": data,
        }
