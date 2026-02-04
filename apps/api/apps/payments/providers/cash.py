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

        Cash payments succeed immediately - no external processing needed.
        The idempotency_key is used as provider_reference for consistency.
        """
        return PaymentResult(
            provider_reference=idempotency_key,
            status=ProviderStatus.SUCCESS,
            redirect_url=None,
            error_code=None,
            error_message=None,
            raw_response={"type": "cash", "amount": amount, "currency": currency},
        )

    def check_status(self, provider_reference: str) -> PaymentResult:
        """
        Check the status of a cash payment.

        Cash payment status is tracked in our database, not with an
        external provider. Looks up the Payment by provider_reference.
        """
        from apps.payments.models import Payment, PaymentStatus

        # Status mapping from Payment model to Provider status
        status_map = {
            PaymentStatus.PENDING: ProviderStatus.PENDING,
            PaymentStatus.PROCESSING: ProviderStatus.PROCESSING,
            PaymentStatus.SUCCESS: ProviderStatus.SUCCESS,
            PaymentStatus.FAILED: ProviderStatus.FAILED,
            PaymentStatus.EXPIRED: ProviderStatus.EXPIRED,
            PaymentStatus.REFUNDED: ProviderStatus.SUCCESS,  # Still successful
            PaymentStatus.PARTIALLY_REFUNDED: ProviderStatus.SUCCESS,
        }

        try:
            payment = Payment.all_objects.get(provider_reference=provider_reference)
            return PaymentResult(
                provider_reference=provider_reference,
                status=status_map.get(payment.status, ProviderStatus.PENDING),
                raw_response={"payment_id": str(payment.id), "status": payment.status},
            )
        except Payment.DoesNotExist:
            return PaymentResult(
                provider_reference=provider_reference,
                status=ProviderStatus.PENDING,
                raw_response={"note": "Payment not found"},
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
