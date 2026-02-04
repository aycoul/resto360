"""Payment services including idempotency handling."""

from typing import TYPE_CHECKING, Optional

from django.core.cache import cache

if TYPE_CHECKING:
    from .models import Payment

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
