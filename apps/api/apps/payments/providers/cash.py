"""Cash payment provider."""

import uuid
from typing import Optional

from .base import PaymentProvider, PaymentResult, ProviderStatus, RefundResult


class CashProvider(PaymentProvider):
    """
    Payment provider for cash transactions.

    Cash payments are handled locally without external API calls.
    They are marked as successful immediately upon confirmation.
    """

    @property
    def provider_code(self) -> str:
        """Return the provider code."""
        return "cash"

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
        Initiate a cash payment.

        Cash payments don't require external processing - they are
        initiated in PENDING state and marked SUCCESS when cashier
        confirms cash received.
        """
        return PaymentResult(
            provider_reference=f"cash_{uuid.uuid4().hex[:12]}",
            status=ProviderStatus.PENDING,
            redirect_url=None,
            error_code=None,
            error_message=None,
            raw_response={"type": "cash", "amount": amount, "currency": currency},
        )

    def check_status(self, provider_reference: str) -> PaymentResult:
        """
        Check the status of a cash payment.

        Cash payment status is tracked in our database, not with an
        external provider. This returns the current known status.
        """
        # For cash, we don't have external status - return pending
        # The actual status comes from our Payment model
        return PaymentResult(
            provider_reference=provider_reference,
            status=ProviderStatus.PENDING,
            raw_response={"note": "Cash status tracked internally"},
        )

    def process_refund(
        self, provider_reference: str, amount: Optional[int] = None
    ) -> RefundResult:
        """
        Process a cash refund.

        Cash refunds are handled manually - this just records that
        a refund should be given.
        """
        return RefundResult(
            success=True,
            provider_reference=f"cash_refund_{uuid.uuid4().hex[:12]}",
            error_message=None,
        )

    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """
        Verify a webhook request.

        Cash payments don't use webhooks - always return True
        for internal status updates.
        """
        return True

    def parse_webhook(self, body: bytes) -> dict:
        """
        Parse a webhook request.

        Cash payments don't use webhooks.
        """
        return {}
