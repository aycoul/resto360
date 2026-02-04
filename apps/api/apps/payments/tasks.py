"""Celery tasks for payment processing."""

import json
import logging

from celery import shared_task

from apps.payments.providers import get_provider
from apps.payments.webhooks.handlers import handle_wave_webhook

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def process_webhook_event(
    self,
    provider_code: str,
    headers: dict,
    body: str,
) -> dict:
    """
    Process a webhook event asynchronously.

    This task is queued when a webhook is received to avoid
    blocking the HTTP response. The actual processing happens
    in the background.

    Args:
        self: Celery task instance (for retries)
        provider_code: The payment provider (e.g., 'wave')
        headers: Request headers for signature verification
        body: Raw request body as string

    Returns:
        dict with processing result
    """
    logger.info("Processing %s webhook event", provider_code)

    try:
        # Get the provider
        provider = get_provider(provider_code)
    except ValueError as e:
        logger.error("Unknown provider for webhook: %s", provider_code)
        return {"success": False, "error": str(e)}

    # Convert body to bytes for verification
    body_bytes = body.encode("utf-8") if isinstance(body, str) else body

    # Verify webhook signature
    if not provider.verify_webhook(headers, body_bytes):
        logger.warning("Webhook signature verification failed for %s", provider_code)
        return {"success": False, "error": "Invalid signature"}

    # Parse webhook payload
    webhook_data = provider.parse_webhook(body_bytes)

    if "error" in webhook_data:
        logger.error("Failed to parse webhook: %s", webhook_data.get("error"))
        return {"success": False, "error": webhook_data.get("error")}

    # Route to appropriate handler based on provider
    result = None
    if provider_code == "wave":
        result = handle_wave_webhook(webhook_data)

    if result:
        return {
            "success": True,
            "payment_id": str(result.id),
            "status": result.status,
        }
    else:
        return {
            "success": True,
            "message": "No action taken (payment not found or already processed)",
        }


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=300,
)
def check_pending_payments(self, provider_code: str) -> dict:
    """
    Check status of pending payments for a provider.

    This task can be run periodically to catch any missed webhooks
    or to verify payment status.

    Args:
        self: Celery task instance
        provider_code: The payment provider to check

    Returns:
        dict with check results
    """
    from apps.payments.models import Payment, PaymentStatus

    logger.info("Checking pending payments for %s", provider_code)

    try:
        provider = get_provider(provider_code)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    # Find pending payments for this provider
    pending_payments = Payment.all_objects.filter(
        provider_code=provider_code,
        status__in=[PaymentStatus.PENDING, PaymentStatus.PROCESSING],
    )

    updated = 0
    for payment in pending_payments:
        try:
            result = provider.check_status(payment.provider_reference)

            # Only update if status has changed
            from apps.payments.providers.base import ProviderStatus

            if result.status == ProviderStatus.SUCCESS:
                if payment.status == PaymentStatus.PENDING:
                    payment.start_processing()
                payment.mark_success()
                payment.provider_response = result.raw_response or {}
                payment.save()
                updated += 1
                logger.info("Payment %s marked SUCCESS", payment.idempotency_key)

            elif result.status == ProviderStatus.EXPIRED:
                if payment.status == PaymentStatus.PENDING:
                    payment.start_processing()
                payment.mark_expired()
                payment.provider_response = result.raw_response or {}
                payment.save()
                updated += 1
                logger.info("Payment %s marked EXPIRED", payment.idempotency_key)

            elif result.status == ProviderStatus.FAILED:
                if payment.status == PaymentStatus.PENDING:
                    payment.start_processing()
                payment.mark_failed(
                    error_code=result.error_code or "unknown",
                    error_message=result.error_message or "Payment failed",
                )
                payment.provider_response = result.raw_response or {}
                payment.save()
                updated += 1
                logger.info("Payment %s marked FAILED", payment.idempotency_key)

        except Exception as e:
            logger.error(
                "Error checking payment %s: %s",
                payment.idempotency_key,
                str(e),
            )

    return {
        "success": True,
        "checked": pending_payments.count(),
        "updated": updated,
    }
