"""Celery tasks for payment processing."""

import logging

from celery import shared_task

from apps.payments.providers import get_provider
from apps.payments.providers.base import ProviderStatus
from apps.payments.webhooks.handlers import (
    handle_digitalpaye_webhook,
    handle_mtn_webhook,
    handle_orange_webhook,
    handle_wave_webhook,
)

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
    elif provider_code == "orange":
        result = handle_orange_webhook(webhook_data)
    elif provider_code == "mtn":
        result = handle_mtn_webhook(webhook_data)
    elif provider_code in ("digitalpaye", "digitalpaye_wave", "digitalpaye_orange", "digitalpaye_mtn"):
        result = handle_digitalpaye_webhook(webhook_data)

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


@shared_task(
    bind=True,
    max_retries=30,  # 30 retries at 2 min intervals = 1 hour total
    default_retry_delay=120,  # 2 minutes between retries
)
def poll_payment_status(self, payment_id: str) -> dict:
    """
    Poll payment provider for status update.

    This is a fallback mechanism for providers with unreliable webhooks
    (Orange Money) or no webhook support in sandbox (MTN MoMo).

    The task will retry up to 30 times (1 hour total at 2 min intervals)
    until the payment reaches a terminal state.

    Args:
        self: Celery task instance (for retries)
        payment_id: UUID of the Payment to poll

    Returns:
        dict with polling result
    """
    from apps.payments.models import Payment, PaymentStatus

    logger.info("Polling payment status for payment_id=%s", payment_id)

    # Find the payment
    try:
        payment = Payment.all_objects.get(id=payment_id)
    except Payment.DoesNotExist:
        logger.warning("Payment not found for poll: %s", payment_id)
        return {"success": False, "error": "Payment not found"}

    # Only poll PROCESSING payments (not PENDING, SUCCESS, FAILED, etc.)
    if payment.status != PaymentStatus.PROCESSING:
        logger.info(
            "Payment %s not in PROCESSING state (status=%s), skipping poll",
            payment.idempotency_key,
            payment.status,
        )
        return {
            "success": True,
            "message": f"Payment not in PROCESSING state, current status: {payment.status}",
        }

    # Get the provider and check status
    try:
        provider = get_provider(payment.provider_code)
    except ValueError as e:
        logger.error("Unknown provider for payment %s: %s", payment_id, payment.provider_code)
        return {"success": False, "error": str(e)}

    try:
        result = provider.check_status(payment.provider_reference)
    except Exception as e:
        logger.error(
            "Error polling payment %s: %s",
            payment.idempotency_key,
            str(e),
        )
        # Retry on error
        raise self.retry(exc=e)

    # Update payment based on provider status
    if result.status == ProviderStatus.SUCCESS:
        payment.mark_success()
        payment.provider_response = result.raw_response or {}
        payment.save()
        logger.info("Payment %s marked SUCCESS via polling", payment.idempotency_key)
        return {
            "success": True,
            "payment_id": str(payment.id),
            "status": "success",
        }

    elif result.status == ProviderStatus.FAILED:
        payment.mark_failed(
            error_code=result.error_code or "unknown",
            error_message=result.error_message or "Payment failed",
        )
        payment.provider_response = result.raw_response or {}
        payment.save()
        logger.info("Payment %s marked FAILED via polling", payment.idempotency_key)
        return {
            "success": True,
            "payment_id": str(payment.id),
            "status": "failed",
        }

    elif result.status == ProviderStatus.EXPIRED:
        payment.mark_expired()
        payment.provider_response = result.raw_response or {}
        payment.save()
        logger.info("Payment %s marked EXPIRED via polling", payment.idempotency_key)
        return {
            "success": True,
            "payment_id": str(payment.id),
            "status": "expired",
        }

    else:
        # Still pending/processing, retry
        logger.info(
            "Payment %s still %s, will retry (attempt %d/%d)",
            payment.idempotency_key,
            result.status.value,
            self.request.retries + 1,
            self.max_retries,
        )
        raise self.retry()
