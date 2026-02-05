"""Tests for order services."""

import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.utils import timezone

from apps.orders.models import DailySequence
from apps.orders.services import calculate_order_totals, get_next_order_number


@pytest.mark.django_db
class TestGetNextOrderNumber:
    """Tests for the get_next_order_number service."""

    def test_first_order_of_day(self, business):
        """Test first order of the day gets number 1."""
        number = get_next_order_number(business)
        assert number == 1

    def test_increments_order_number(self, business):
        """Test order numbers increment correctly."""
        num1 = get_next_order_number(business)
        num2 = get_next_order_number(business)
        num3 = get_next_order_number(business)

        assert num1 == 1
        assert num2 == 2
        assert num3 == 3

    def test_creates_daily_sequence(self, business):
        """Test creates DailySequence record."""
        today = timezone.localdate()
        assert not DailySequence.objects.filter(
            business=business, date=today
        ).exists()

        get_next_order_number(business)

        sequence = DailySequence.objects.get(business=business, date=today)
        assert sequence.last_number == 1

    def test_different_businesses_have_independent_sequences(
        self, business_factory
    ):
        """Test each business has its own sequence."""
        business_a = business_factory()
        business_b = business_factory()

        num_a1 = get_next_order_number(business_a)
        num_a2 = get_next_order_number(business_a)
        num_b1 = get_next_order_number(business_b)

        assert num_a1 == 1
        assert num_a2 == 2
        assert num_b1 == 1  # Independent sequence for business B

    def test_continues_existing_sequence(self, business):
        """Test continues from existing sequence number."""
        today = timezone.localdate()
        DailySequence.objects.create(
            business=business,
            date=today,
            last_number=10,
        )

        number = get_next_order_number(business)
        assert number == 11

    @pytest.mark.django_db(transaction=True)
    def test_concurrent_order_numbers(self, business):
        """Test concurrent calls get unique order numbers."""
        # Skip if not using PostgreSQL (SQLite doesn't support SELECT FOR UPDATE)
        from django.db import connection
        if 'sqlite' in connection.vendor:
            pytest.skip("SELECT FOR UPDATE not supported in SQLite")

        results = []

        def get_number():
            return get_next_order_number(business)

        # Execute 10 concurrent order number requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_number) for _ in range(10)]
            for future in as_completed(futures):
                results.append(future.result())

        # All numbers should be unique
        assert len(set(results)) == 10
        assert sorted(results) == list(range(1, 11))


@pytest.mark.django_db
class TestCalculateOrderTotals:
    """Tests for the calculate_order_totals service."""

    def test_calculates_subtotal(self, order_factory, order_item_factory):
        """Test calculates subtotal from items."""
        order = order_factory(subtotal=0, total=0, discount=0)
        order_item_factory(
            order=order,
            business=order.business,
            unit_price=5000,
            quantity=2,
            modifiers_total=0,
            line_total=10000,
        )
        order_item_factory(
            order=order,
            business=order.business,
            unit_price=2000,
            quantity=1,
            modifiers_total=0,
            line_total=2000,
        )

        calculate_order_totals(order)
        order.refresh_from_db()

        assert order.subtotal == 12000
        assert order.total == 12000

    def test_applies_discount(self, order_factory, order_item_factory):
        """Test discount is applied to total."""
        order = order_factory(subtotal=0, total=0, discount=1000)
        order_item_factory(
            order=order,
            business=order.business,
            unit_price=5000,
            quantity=1,
            modifiers_total=0,
            line_total=5000,
        )

        calculate_order_totals(order)
        order.refresh_from_db()

        assert order.subtotal == 5000
        assert order.total == 4000  # 5000 - 1000 discount

    def test_total_not_negative(self, order_factory, order_item_factory):
        """Test total cannot be negative even with large discount."""
        order = order_factory(subtotal=0, total=0, discount=10000)
        order_item_factory(
            order=order,
            business=order.business,
            unit_price=5000,
            quantity=1,
            modifiers_total=0,
            line_total=5000,
        )

        calculate_order_totals(order)
        order.refresh_from_db()

        assert order.subtotal == 5000
        assert order.total == 0  # Clamped to 0, not -5000
