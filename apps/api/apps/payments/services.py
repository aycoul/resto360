"""Payment services including idempotency handling and orchestration."""

import logging
from typing import TYPE_CHECKING, Any, Optional

from django.core.cache import cache
from django.db import transaction

if TYPE_CHECKING:
    from apps.authentication.models import Business
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
            business=order.business,
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
    business: "Business",
) -> Optional[dict]:
    """
    Get the current status of a payment.

    Args:
        payment_id: UUID of the payment
        business: Business for tenant isolation

    Returns:
        dict with payment status info, or None if not found
    """
    from .models import Payment

    try:
        payment = Payment.objects.filter(
            business=business,
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


def get_daily_reconciliation(business: "Business", date=None) -> dict:
    """
    Generate daily payment reconciliation report.

    Args:
        business: Business instance
        date: Date to report on (defaults to today)

    Returns:
        dict with by_provider breakdown, totals, refunds, and net_amount
    """
    from datetime import timedelta

    from django.db.models import Count, Sum
    from django.utils import timezone

    from .models import Payment, PaymentStatus

    if date is None:
        date = timezone.localdate()

    # Build datetime range for the day
    start = timezone.make_aware(
        timezone.datetime.combine(date, timezone.datetime.min.time())
    )
    end = start + timedelta(days=1)

    # Get successful payments for the day
    payments = Payment.all_objects.filter(
        business=business,
        status=PaymentStatus.SUCCESS,
        completed_at__gte=start,
        completed_at__lt=end,
    )

    # Aggregate by provider
    by_provider = payments.values("provider_code").annotate(
        count=Count("id"),
        total=Sum("amount"),
    ).order_by("provider_code")

    # Format provider names
    provider_names = {
        "wave": "Wave Money",
        "orange": "Orange Money",
        "mtn": "MTN MoMo",
        "cash": "Cash",
    }

    by_provider_formatted = [
        {
            "provider_code": item["provider_code"],
            "provider_name": provider_names.get(item["provider_code"], item["provider_code"]),
            "count": item["count"],
            "total": item["total"] or 0,
        }
        for item in by_provider
    ]

    # Calculate totals
    totals = payments.aggregate(
        total_count=Count("id"),
        total_amount=Sum("amount"),
    )

    # Get refunds (same day)
    refunds = Payment.all_objects.filter(
        business=business,
        status__in=[PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED],
        completed_at__gte=start,
        completed_at__lt=end,
    ).aggregate(
        refund_count=Count("id"),
        refund_amount=Sum("refunded_amount"),
    )

    # Get pending payments (initiated but not completed)
    pending = Payment.all_objects.filter(
        business=business,
        status=PaymentStatus.PROCESSING,
        initiated_at__gte=start,
        initiated_at__lt=end,
    ).aggregate(
        pending_count=Count("id"),
        pending_amount=Sum("amount"),
    )

    # Get failed payments
    failed = Payment.all_objects.filter(
        business=business,
        status__in=[PaymentStatus.FAILED, PaymentStatus.EXPIRED],
        initiated_at__gte=start,
        initiated_at__lt=end,
    ).aggregate(
        failed_count=Count("id"),
        failed_amount=Sum("amount"),
    )

    total_amount = totals["total_amount"] or 0
    refund_amount = refunds["refund_amount"] or 0

    return {
        "date": date.isoformat(),
        "business_id": str(business.id),
        "by_provider": by_provider_formatted,
        "totals": {
            "count": totals["total_count"] or 0,
            "amount": total_amount,
        },
        "refunds": {
            "count": refunds["refund_count"] or 0,
            "amount": refund_amount,
        },
        "pending": {
            "count": pending["pending_count"] or 0,
            "amount": pending["pending_amount"] or 0,
        },
        "failed": {
            "count": failed["failed_count"] or 0,
            "amount": failed["failed_amount"] or 0,
        },
        "net_amount": total_amount - refund_amount,
    }


def get_reconciliation_range(business: "Business", start_date, end_date) -> list:
    """
    Get reconciliation for a date range (max 90 days).

    Args:
        business: Business instance
        start_date: Start date for the range
        end_date: End date for the range

    Returns:
        list of daily reconciliation dicts

    Raises:
        ValueError: If date range exceeds 90 days
    """
    from datetime import timedelta

    # Enforce max 90 days
    if (end_date - start_date).days > 90:
        raise ValueError("Date range cannot exceed 90 days")

    results = []
    current = start_date
    while current <= end_date:
        results.append(get_daily_reconciliation(business, current))
        current += timedelta(days=1)

    return results


def process_refund_request(payment: "Payment", amount: int = None, reason: str = "") -> dict:
    """
    Process a refund request for a payment.

    Args:
        payment: Payment instance
        amount: Refund amount (None = full refund)
        reason: Reason for refund

    Returns:
        dict with success status and details
    """
    from .models import PaymentStatus
    from .providers import get_provider

    # Validate payment can be refunded
    if payment.status not in [PaymentStatus.SUCCESS, PaymentStatus.PARTIALLY_REFUNDED]:
        return {
            "success": False,
            "error": f"Cannot refund payment with status {payment.status}",
        }

    # Determine refund amount
    max_refundable = payment.amount - payment.refunded_amount
    if amount is None:
        amount = max_refundable
    else:
        if amount > max_refundable:
            return {
                "success": False,
                "error": f"Refund amount {amount} exceeds refundable amount {max_refundable}",
            }

    if amount <= 0:
        return {
            "success": False,
            "error": "Refund amount must be positive",
        }

    # Cash refunds are immediate (just mark as refunded)
    if payment.provider_code == "cash":
        new_refunded_total = payment.refunded_amount + amount
        if new_refunded_total == payment.amount:
            payment.mark_refunded()
        else:
            payment.mark_partially_refunded(new_refunded_total)
        payment.provider_response["refund_reason"] = reason
        payment.save()
        return {
            "success": True,
            "refund_type": "full" if payment.status == PaymentStatus.REFUNDED else "partial",
            "refunded_amount": amount,
        }

    # Mobile money refund via provider
    try:
        provider = get_provider(payment.provider_code)
        result = provider.process_refund(payment.provider_reference, amount)
    except Exception as e:
        logger.error(
            "Provider refund failed for payment %s: %s",
            payment.idempotency_key,
            str(e),
        )
        return {
            "success": False,
            "error": str(e),
        }

    if not result.success:
        return {
            "success": False,
            "error": result.error_message or "Provider refund failed",
        }

    # Update payment status
    new_refunded_total = payment.refunded_amount + amount
    if new_refunded_total == payment.amount:
        payment.mark_refunded()
    else:
        payment.mark_partially_refunded(new_refunded_total)

    payment.provider_response["refund_reference"] = result.provider_reference
    payment.provider_response["refund_reason"] = reason
    payment.save()

    return {
        "success": True,
        "refund_type": "full" if payment.status == PaymentStatus.REFUNDED else "partial",
        "refunded_amount": amount,
        "provider_reference": result.provider_reference,
    }
