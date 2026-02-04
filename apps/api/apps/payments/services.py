"""Payment services including idempotency handling and orchestration."""

import logging
from typing import TYPE_CHECKING, Any, Optional

from django.core.cache import cache
from django.db import transaction

if TYPE_CHECKING:
    from apps.authentication.models import Restaurant
    from apps.orders.models import Order

    from .models import Payment, PaymentMethod

logger = logging.getLogger(__name__)

# Idempotency lock time-to-live (24 hours in seconds)
IDEMPOTENCY_TTL = 86400


def get_idempotency_lock_key(key: str) -> str:
    """
    Get the cache key for an idempotency lock.

    Args:
        key: The idempotency key

    Returns:
        Cache key string
    """
    return f"payment:idempotency:{key}"


def check_idempotency(idempotency_key: str) -> Optional["Payment"]:
    """
    Check if a payment already exists for this idempotency key.

    First checks the cache (fast path), then the database (slow path).
    If found in DB but not cache, populates the cache.

    Args:
        idempotency_key: The idempotency key to check

    Returns:
        Existing Payment if found, None otherwise
    """
    from .models import Payment

    cache_key = get_idempotency_lock_key(idempotency_key)

    # Fast path: check cache first
    cached_payment_id = cache.get(cache_key)
    if cached_payment_id:
        try:
            return Payment.all_objects.get(id=cached_payment_id)
        except Payment.DoesNotExist:
            # Cache has stale data - clear it
            cache.delete(cache_key)

    # Slow path: check database
    try:
        payment = Payment.all_objects.get(idempotency_key=idempotency_key)
        # Populate cache for future requests
        cache.set(cache_key, str(payment.id), IDEMPOTENCY_TTL)
        return payment
    except Payment.DoesNotExist:
        return None


def acquire_idempotency_lock(idempotency_key: str, payment_id: str) -> bool:
    """
    Acquire an idempotency lock for creating a new payment.

    Uses Redis SETNX via cache.add() for atomic lock acquisition.

    Args:
        idempotency_key: The idempotency key
        payment_id: The payment ID to associate with this key

    Returns:
        True if lock acquired, False if key already exists
    """
    cache_key = get_idempotency_lock_key(idempotency_key)

    # cache.add() is atomic (uses SETNX in Redis)
    # Returns True if key was set, False if it already existed
    return cache.add(cache_key, payment_id, IDEMPOTENCY_TTL)


def release_idempotency_lock(idempotency_key: str) -> None:
    """
    Release an idempotency lock (for cleanup on failure).

    Args:
        idempotency_key: The idempotency key to release
    """
    cache_key = get_idempotency_lock_key(idempotency_key)
    cache.delete(cache_key)


def initiate_payment(
    order: "Order",
    payment_method: "PaymentMethod",
    idempotency_key: str,
    request: Any = None,
    callback_url: str = "",
    success_url: str = "",
    error_url: str = "",
) -> dict:
    """
    Initiate a payment for an order.

    Orchestrates the payment flow:
    1. Check idempotency - return existing payment if found
    2. Get provider via get_provider(provider_code)
    3. Create Payment record in transaction.atomic()
    4. Acquire idempotency lock
    5. Call provider.initiate_payment()
    6. Update payment with provider response
    7. For cash: mark_success() immediately
    8. For mobile money: start_processing(), schedule polling for orange/mtn

    Args:
        order: The order being paid
        payment_method: The payment method to use
        idempotency_key: Unique key to prevent duplicate payments
        request: The HTTP request (for building callback URLs)
        callback_url: URL for webhook notifications
        success_url: URL to redirect after successful payment
        error_url: URL to redirect after failed payment

    Returns:
        dict with:
            - payment: Payment instance
            - redirect_url: URL to redirect customer (mobile money only)
            - status: Current payment status
            - is_duplicate: True if existing payment was returned
    """
    from .models import Payment, PaymentStatus
    from .providers import get_provider

    # Step 1: Check idempotency - return existing payment if found
    existing_payment = check_idempotency(idempotency_key)
    if existing_payment:
        logger.info(
            "Returning existing payment for idempotency_key=%s",
            idempotency_key,
        )
        return {
            "payment": existing_payment,
            "redirect_url": existing_payment.provider_response.get("redirect_url"),
            "status": existing_payment.status,
            "is_duplicate": True,
        }

    # Step 2: Get provider
    provider_code = payment_method.provider_code
    provider = get_provider(provider_code)

    # Step 3 & 4: Create Payment record with idempotency lock
    with transaction.atomic():
        # Create the payment record first
        payment = Payment.objects.create(
            restaurant=order.restaurant,
            order=order,
            payment_method=payment_method,
            amount=order.total,
            idempotency_key=idempotency_key,
            provider_code=provider_code,
        )

        # Acquire idempotency lock
        if not acquire_idempotency_lock(idempotency_key, str(payment.id)):
            # Race condition: another request created a payment
            # Rollback this transaction and return the existing one
            existing = check_idempotency(idempotency_key)
            if existing:
                return {
                    "payment": existing,
                    "redirect_url": existing.provider_response.get("redirect_url"),
                    "status": existing.status,
                    "is_duplicate": True,
                }

    # Step 5: Call provider.initiate_payment()
    customer_phone = order.customer_phone or ""

    try:
        result = provider.initiate_payment(
            amount=order.total,
            currency="XOF",
            order_reference=str(order.id),
            customer_phone=customer_phone,
            idempotency_key=idempotency_key,
            callback_url=callback_url,
            success_url=success_url,
            error_url=error_url,
        )
    except Exception as e:
        logger.error(
            "Provider initiate_payment failed for payment %s: %s",
            payment.idempotency_key,
            str(e),
        )
        # Mark payment as failed
        with transaction.atomic():
            payment = Payment.all_objects.select_for_update().get(pk=payment.pk)
            payment.start_processing()
            payment.mark_failed(
                error_code="provider_error",
                error_message=str(e),
            )
            payment.save()
        return {
            "payment": payment,
            "redirect_url": None,
            "status": payment.status,
            "is_duplicate": False,
        }

    # Step 6: Update payment with provider response
    with transaction.atomic():
        payment = Payment.all_objects.select_for_update().get(pk=payment.pk)
        payment.provider_reference = result.provider_reference
        payment.provider_response = result.raw_response or {}

        # Store redirect_url in provider_response for idempotent retrieval
        if result.redirect_url:
            payment.provider_response["redirect_url"] = result.redirect_url

        # Step 7: Handle cash - mark_success() immediately
        if provider_code == "cash":
            payment.start_processing()
            payment.mark_success()
            payment.save()
            logger.info("Cash payment %s completed immediately", payment.idempotency_key)
            return {
                "payment": payment,
                "redirect_url": None,
                "status": payment.status,
                "is_duplicate": False,
            }

        # Step 8: Handle mobile money - start_processing, schedule polling
        payment.start_processing()
        payment.save()

    # Schedule polling for Orange and MTN (unreliable webhooks)
    if provider_code in ("orange", "mtn"):
        from .tasks import poll_payment_status

        # Schedule polling task
        poll_payment_status.apply_async(
            args=[str(payment.id)],
            countdown=30,  # First poll after 30 seconds
        )
        logger.info(
            "Scheduled polling for %s payment %s",
            provider_code,
            payment.idempotency_key,
        )

    return {
        "payment": payment,
        "redirect_url": result.redirect_url,
        "status": payment.status,
        "is_duplicate": False,
    }


def get_payment_status(
    payment_id: str,
    restaurant: "Restaurant",
) -> Optional[dict]:
    """
    Get the current status of a payment.

    Args:
        payment_id: UUID of the payment
        restaurant: Restaurant for tenant isolation

    Returns:
        dict with payment status info, or None if not found
    """
    from .models import Payment

    try:
        payment = Payment.objects.filter(
            restaurant=restaurant,
            id=payment_id,
        ).first()

        if not payment:
            return None

        return {
            "id": str(payment.id),
            "order_id": str(payment.order_id),
            "amount": payment.amount,
            "status": payment.status,
            "provider_code": payment.provider_code,
            "provider_reference": payment.provider_reference,
            "initiated_at": payment.initiated_at.isoformat() if payment.initiated_at else None,
            "completed_at": payment.completed_at.isoformat() if payment.completed_at else None,
            "error_code": payment.error_code,
            "error_message": payment.error_message,
        }
    except Exception as e:
        logger.error("Error getting payment status for %s: %s", payment_id, str(e))
        return None
