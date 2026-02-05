"""Tests for payment services."""

import pytest
from django.core.cache import cache

from apps.payments.services import (
    IDEMPOTENCY_TTL,
    acquire_idempotency_lock,
    check_idempotency,
    get_idempotency_lock_key,
    release_idempotency_lock,
)

from .factories import PaymentFactory


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before and after each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestIdempotencyKey:
    """Tests for idempotency key generation."""

    def test_get_idempotency_lock_key(self):
        """Test that idempotency lock key is generated correctly."""
        key = get_idempotency_lock_key("test_key_123")
        assert key == "payment:idempotency:test_key_123"

    def test_get_idempotency_lock_key_with_special_chars(self):
        """Test idempotency key with special characters."""
        key = get_idempotency_lock_key("order-123-pay-456")
        assert key == "payment:idempotency:order-123-pay-456"


@pytest.mark.django_db
class TestCheckIdempotency:
    """Tests for check_idempotency function."""

    def test_check_idempotency_returns_none_for_new_key(self):
        """Test that check_idempotency returns None for a new key."""
        result = check_idempotency("brand_new_key")
        assert result is None

    def test_check_idempotency_returns_payment_for_existing_key(self, owner):
        """Test that check_idempotency returns existing payment."""
        from apps.orders.tests.factories import OrderFactory

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            idempotency_key="existing_key_123",
        )

        result = check_idempotency("existing_key_123")

        assert result is not None
        assert result.id == payment.id
        assert result.idempotency_key == "existing_key_123"

    def test_check_idempotency_populates_cache_from_db(self, owner):
        """Test that check_idempotency populates cache when found in DB."""
        from apps.orders.tests.factories import OrderFactory

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            idempotency_key="db_only_key",
        )

        # Ensure cache is empty
        cache_key = get_idempotency_lock_key("db_only_key")
        assert cache.get(cache_key) is None

        # Check idempotency (should find in DB)
        result = check_idempotency("db_only_key")
        assert result is not None

        # Now cache should be populated
        cached_value = cache.get(cache_key)
        assert cached_value == str(payment.id)

    def test_check_idempotency_uses_cache_first(self, owner):
        """Test that check_idempotency uses cache for fast path."""
        from apps.orders.tests.factories import OrderFactory

        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            idempotency_key="cached_key",
        )

        # Pre-populate cache
        cache_key = get_idempotency_lock_key("cached_key")
        cache.set(cache_key, str(payment.id), IDEMPOTENCY_TTL)

        # Check should use cache and return the payment
        result = check_idempotency("cached_key")
        assert result is not None
        assert result.id == payment.id


@pytest.mark.django_db
class TestAcquireIdempotencyLock:
    """Tests for acquire_idempotency_lock function."""

    def test_acquire_idempotency_lock_succeeds_for_new_key(self):
        """Test that lock can be acquired for a new key."""
        result = acquire_idempotency_lock("new_lock_key", "payment_id_123")
        assert result is True

        # Verify it's in cache
        cache_key = get_idempotency_lock_key("new_lock_key")
        assert cache.get(cache_key) == "payment_id_123"

    def test_acquire_idempotency_lock_fails_for_existing_key(self):
        """Test that lock fails if key already exists."""
        # First lock should succeed
        first_result = acquire_idempotency_lock("contested_key", "payment_1")
        assert first_result is True

        # Second lock should fail
        second_result = acquire_idempotency_lock("contested_key", "payment_2")
        assert second_result is False

        # Original value should be preserved
        cache_key = get_idempotency_lock_key("contested_key")
        assert cache.get(cache_key) == "payment_1"

    def test_acquire_lock_is_atomic(self):
        """Test that lock acquisition is atomic."""
        # This tests the behavior - actual atomicity depends on cache backend
        results = []
        for i in range(5):
            result = acquire_idempotency_lock("atomic_key", f"payment_{i}")
            results.append(result)

        # Only one should succeed
        assert sum(results) == 1
        assert results[0] is True  # First one should succeed


@pytest.mark.django_db
class TestReleaseIdempotencyLock:
    """Tests for release_idempotency_lock function."""

    def test_release_idempotency_lock_removes_from_cache(self):
        """Test that releasing a lock removes it from cache."""
        # Acquire lock
        acquire_idempotency_lock("release_test_key", "payment_123")

        # Verify it exists
        cache_key = get_idempotency_lock_key("release_test_key")
        assert cache.get(cache_key) is not None

        # Release lock
        release_idempotency_lock("release_test_key")

        # Verify it's gone
        assert cache.get(cache_key) is None

    def test_release_nonexistent_lock_is_safe(self):
        """Test that releasing a nonexistent lock doesn't raise errors."""
        # Should not raise any exception
        release_idempotency_lock("nonexistent_key")

    def test_release_allows_new_lock_acquisition(self):
        """Test that after release, a new lock can be acquired."""
        # Acquire and release
        acquire_idempotency_lock("reacquire_key", "payment_1")
        release_idempotency_lock("reacquire_key")

        # Should be able to acquire again
        result = acquire_idempotency_lock("reacquire_key", "payment_2")
        assert result is True

        cache_key = get_idempotency_lock_key("reacquire_key")
        assert cache.get(cache_key) == "payment_2"
