"""Webhook event handlers for all payment providers."""

import logging
from typing import Optional

from django.db import transaction

from apps.payments.models import Payment, PaymentStatus

logger = logging.getLogger(__name__)


# Terminal states - payments in these states should not be updated
TERMINAL_STATES = {
    PaymentStatus.SUCCESS,
    PaymentStatus.FAILED,
    PaymentStatus.EXPIRED,
    PaymentStatus.REFUNDED,
    PaymentStatus.PARTIALLY_REFUNDED,
}


def handle_wave_webhook(webhook_data: dict) -> Optional[Payment]:
    """
    Handle a Wave webhook event.

    Updates the Payment status based on the webhook event type.
    This handler is idempotent - processing the same event twice
    will not cause duplicate updates.

    Args:
        webhook_data: Normalized webhook data from WaveProvider.parse_webhook()
            - event_type: Type of event (checkout.session.completed, etc.)
            - payment_reference: The checkout session ID
            - status: Normalized status (success, expired, failed)
            - client_reference: Our order reference

    Returns:
        Updated Payment instance, or None if payment not found/already processed
    """
    event_type = webhook_data.get("event_type", "")
    payment_reference = webhook_data.get("payment_reference", "")
    status = webhook_data.get("status", "")

    if not payment_reference:
        logger.warning("Wave webhook missing payment_reference")
        return None

    logger.info(
        "Processing Wave webhook: event=%s, reference=%s, status=%s",
        event_type,
        payment_reference,
        status,
    )

    # Find the payment by provider reference
    try:
        payment = Payment.all_objects.select_for_update().get(
            provider_reference=payment_reference
        )
    except Payment.DoesNotExist:
        logger.warning("Payment not found for provider_reference: %s", payment_reference)
        return None
    except Payment.MultipleObjectsReturned:
        logger.error("Multiple payments found for provider_reference: %s", payment_reference)
        return None

    # Check if payment is in a terminal state (idempotency)
    if payment.status in TERMINAL_STATES:
        logger.info(
            "Payment %s already in terminal state: %s",
            payment.idempotency_key,
            payment.status,
        )
        return payment

    # Apply status transition based on webhook status
    with transaction.atomic():
        # Re-fetch with lock if not already locked
        payment = Payment.all_objects.select_for_update().get(pk=payment.pk)

        # Check again after lock (double-check locking)
        if payment.status in TERMINAL_STATES:
            return payment

        # Ensure payment is in PROCESSING state before transitioning
        if payment.status == PaymentStatus.PENDING:
            payment.start_processing()
            payment.save()

        if status == "success":
            payment.mark_success()
            payment.provider_response = webhook_data.get("raw", {})
            payment.save()
            logger.info("Payment %s marked as SUCCESS", payment.idempotency_key)

        elif status == "expired":
            payment.mark_expired()
            payment.provider_response = webhook_data.get("raw", {})
            payment.save()
            logger.info("Payment %s marked as EXPIRED", payment.idempotency_key)

        elif status == "failed":
            error_data = webhook_data.get("raw", {})
            payment.mark_failed(
                error_code=error_data.get("error_code", "unknown"),
                error_message=error_data.get("error_message", "Payment failed"),
            )
            payment.provider_response = error_data
            payment.save()
            logger.info("Payment %s marked as FAILED", payment.idempotency_key)

        else:
            logger.warning(
                "Unknown webhook status %s for payment %s",
                status,
                payment.idempotency_key,
            )
            return None

    return payment


def handle_orange_webhook(webhook_data: dict) -> Optional[Payment]:
    """
    Handle an Orange Money webhook event.

    TODO: Implement in 04-03-PLAN.md (Orange Money provider)

    Args:
        webhook_data: Normalized webhook data from OrangeProvider.parse_webhook()

    Returns:
        Updated Payment instance, or None if payment not found/already processed
    """
    logger.warning("Orange webhook handler not yet implemented")
    return None


def handle_mtn_webhook(webhook_data: dict) -> Optional[Payment]:
    """
    Handle an MTN MoMo webhook event.

    TODO: Implement in 04-04-PLAN.md (MTN MoMo provider)

    Args:
        webhook_data: Normalized webhook data from MTNProvider.parse_webhook()

    Returns:
        Updated Payment instance, or None if payment not found/already processed
    """
    logger.warning("MTN webhook handler not yet implemented")
    return None
