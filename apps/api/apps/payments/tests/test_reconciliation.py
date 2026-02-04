"""Tests for payment reconciliation functionality."""

from datetime import date, timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.payments.models import Payment, PaymentStatus
from apps.payments.services import get_daily_reconciliation, get_reconciliation_range
from apps.payments.tests.factories import PaymentFactory, PaymentMethodFactory


@pytest.mark.django_db
class TestDailyReconciliation:
    """Tests for get_daily_reconciliation service."""

    def test_daily_reconciliation_empty(self, owner):
        """Test reconciliation with no payments for the day."""
        result = get_daily_reconciliation(owner.restaurant)

        assert result["totals"]["count"] == 0
        assert result["totals"]["amount"] == 0
        assert result["refunds"]["count"] == 0
        assert result["refunds"]["amount"] == 0
        assert result["pending"]["count"] == 0
        assert result["failed"]["count"] == 0
        assert result["net_amount"] == 0
        assert result["by_provider"] == []

    @freeze_time("2026-02-04 12:00:00")
    def test_daily_reconciliation_single_provider(self, owner):
        """Test reconciliation with single provider (cash)."""
        from apps.orders.tests.factories import OrderFactory

        # Create payment method
        payment_method = PaymentMethodFactory(
            restaurant=owner.restaurant,
            provider_code="cash",
            name="Cash",
        )

        # Create 3 successful cash payments
        for i, amount in enumerate([10000, 15000, 5000]):
            order = OrderFactory(restaurant=owner.restaurant, cashier=owner)
            payment = PaymentFactory(
                restaurant=owner.restaurant,
                order=order,
                payment_method=payment_method,
                amount=amount,
                provider_code="cash",
                idempotency_key=f"idem-single-{i}",
            )
            # Transition to SUCCESS
            payment.start_processing()
            payment.mark_success()
            payment.save()

        result = get_daily_reconciliation(owner.restaurant)

        assert len(result["by_provider"]) == 1
        assert result["by_provider"][0]["provider_code"] == "cash"
        assert result["by_provider"][0]["count"] == 3
        assert result["by_provider"][0]["total"] == 30000
        assert result["totals"]["count"] == 3
        assert result["totals"]["amount"] == 30000
        assert result["net_amount"] == 30000

    @freeze_time("2026-02-04 12:00:00")
    def test_daily_reconciliation_multiple_providers(self, owner):
        """Test reconciliation with multiple providers."""
        from apps.orders.tests.factories import OrderFactory

        # Create payment methods
        cash_method = PaymentMethodFactory(
            restaurant=owner.restaurant,
            provider_code="cash",
            name="Cash",
        )
        wave_method = PaymentMethodFactory(
            restaurant=owner.restaurant,
            provider_code="wave",
            name="Wave Money",
        )

        # Create 2 cash payments totaling 20000
        for i, amount in enumerate([10000, 10000]):
            order = OrderFactory(restaurant=owner.restaurant, cashier=owner)
            payment = PaymentFactory(
                restaurant=owner.restaurant,
                order=order,
                payment_method=cash_method,
                amount=amount,
                provider_code="cash",
                idempotency_key=f"idem-multi-cash-{i}",
            )
            payment.start_processing()
            payment.mark_success()
            payment.save()

        # Create 3 wave payments totaling 45000
        for i, amount in enumerate([15000, 15000, 15000]):
            order = OrderFactory(restaurant=owner.restaurant, cashier=owner)
            payment = PaymentFactory(
                restaurant=owner.restaurant,
                order=order,
                payment_method=wave_method,
                amount=amount,
                provider_code="wave",
                idempotency_key=f"idem-multi-wave-{i}",
            )
            payment.start_processing()
            payment.mark_success()
            payment.save()

        result = get_daily_reconciliation(owner.restaurant)

        assert len(result["by_provider"]) == 2
        assert result["totals"]["count"] == 5
        assert result["totals"]["amount"] == 65000
        assert result["net_amount"] == 65000

        # Check individual providers
        providers = {p["provider_code"]: p for p in result["by_provider"]}
        assert providers["cash"]["count"] == 2
        assert providers["cash"]["total"] == 20000
        assert providers["wave"]["count"] == 3
        assert providers["wave"]["total"] == 45000

    @freeze_time("2026-02-04 12:00:00")
    def test_reconciliation_includes_refunds(self, owner):
        """Test that refunds are included in reconciliation."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            restaurant=owner.restaurant,
            provider_code="cash",
            name="Cash",
        )

        order = OrderFactory(restaurant=owner.restaurant, cashier=owner)
        payment = PaymentFactory(
            restaurant=owner.restaurant,
            order=order,
            payment_method=payment_method,
            amount=10000,
            provider_code="cash",
            idempotency_key="idem-refund-test",
        )
        # Complete payment then refund it
        payment.start_processing()
        payment.mark_success()
        payment.mark_refunded()
        payment.save()

        result = get_daily_reconciliation(owner.restaurant)

        # Refund status payments are tracked in refunds section
        # Note: Once refunded, status is REFUNDED not SUCCESS, so totals.count=0
        assert result["refunds"]["count"] == 1
        assert result["refunds"]["amount"] == 10000
        # totals only counts SUCCESS payments, so 0 here
        assert result["totals"]["count"] == 0
        # net_amount = totals.amount - refunds.amount = 0 - 10000 = -10000
        # This is expected behavior - the refund shows as negative net for the day
        assert result["net_amount"] == -10000

    @freeze_time("2026-02-04 12:00:00")
    def test_reconciliation_date_filter(self, owner):
        """Test that reconciliation filters by date correctly."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            restaurant=owner.restaurant,
            provider_code="cash",
            name="Cash",
        )

        # Create payment on 2026-02-03 (yesterday)
        with freeze_time("2026-02-03 12:00:00"):
            order1 = OrderFactory(restaurant=owner.restaurant, cashier=owner)
            payment1 = PaymentFactory(
                restaurant=owner.restaurant,
                order=order1,
                payment_method=payment_method,
                amount=5000,
                provider_code="cash",
                idempotency_key="idem-date-yesterday",
            )
            payment1.start_processing()
            payment1.mark_success()
            payment1.save()

        # Create payment on 2026-02-04 (today)
        with freeze_time("2026-02-04 12:00:00"):
            order2 = OrderFactory(restaurant=owner.restaurant, cashier=owner)
            payment2 = PaymentFactory(
                restaurant=owner.restaurant,
                order=order2,
                payment_method=payment_method,
                amount=10000,
                provider_code="cash",
                idempotency_key="idem-date-today",
            )
            payment2.start_processing()
            payment2.mark_success()
            payment2.save()

        # Get reconciliation for today (2026-02-04)
        today_result = get_daily_reconciliation(owner.restaurant, date(2026, 2, 4))
        assert today_result["totals"]["count"] == 1
        assert today_result["totals"]["amount"] == 10000

        # Get reconciliation for yesterday (2026-02-03)
        yesterday_result = get_daily_reconciliation(owner.restaurant, date(2026, 2, 3))
        assert yesterday_result["totals"]["count"] == 1
        assert yesterday_result["totals"]["amount"] == 5000

    def test_reconciliation_includes_pending(self, owner):
        """Test that pending payments are tracked separately."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            restaurant=owner.restaurant,
            provider_code="wave",
            name="Wave",
        )

        # Create a processing (pending) payment
        order = OrderFactory(restaurant=owner.restaurant, cashier=owner)
        payment = PaymentFactory(
            restaurant=owner.restaurant,
            order=order,
            payment_method=payment_method,
            amount=15000,
            provider_code="wave",
            idempotency_key="idem-pending",
        )
        payment.start_processing()
        payment.save()

        result = get_daily_reconciliation(owner.restaurant)

        assert result["pending"]["count"] == 1
        assert result["pending"]["amount"] == 15000
        assert result["totals"]["count"] == 0  # Not in successful totals

    def test_reconciliation_includes_failed(self, owner):
        """Test that failed payments are tracked separately."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            restaurant=owner.restaurant,
            provider_code="wave",
            name="Wave",
        )

        # Create a failed payment
        order = OrderFactory(restaurant=owner.restaurant, cashier=owner)
        payment = PaymentFactory(
            restaurant=owner.restaurant,
            order=order,
            payment_method=payment_method,
            amount=20000,
            provider_code="wave",
            idempotency_key="idem-failed",
        )
        payment.start_processing()
        payment.mark_failed(error_code="declined", error_message="Card declined")
        payment.save()

        result = get_daily_reconciliation(owner.restaurant)

        assert result["failed"]["count"] == 1
        assert result["failed"]["amount"] == 20000
        assert result["totals"]["count"] == 0  # Not in successful totals


@pytest.mark.django_db
class TestReconciliationRange:
    """Tests for get_reconciliation_range service."""

    @freeze_time("2026-02-04 12:00:00")
    def test_reconciliation_range(self, owner):
        """Test getting reconciliation for a date range."""
        from apps.orders.tests.factories import OrderFactory

        payment_method = PaymentMethodFactory(
            restaurant=owner.restaurant,
            provider_code="cash",
            name="Cash",
        )

        # Create payments across 3 days
        for i, day in enumerate([2, 3, 4]):
            with freeze_time(f"2026-02-0{day} 12:00:00"):
                order = OrderFactory(restaurant=owner.restaurant, cashier=owner)
                payment = PaymentFactory(
                    restaurant=owner.restaurant,
                    order=order,
                    payment_method=payment_method,
                    amount=10000 * (i + 1),
                    provider_code="cash",
                    idempotency_key=f"idem-range-{day}",
                )
                payment.start_processing()
                payment.mark_success()
                payment.save()

        # Get range report
        results = get_reconciliation_range(
            owner.restaurant,
            date(2026, 2, 2),
            date(2026, 2, 4),
        )

        assert len(results) == 3
        assert results[0]["date"] == "2026-02-02"
        assert results[0]["totals"]["amount"] == 10000
        assert results[1]["date"] == "2026-02-03"
        assert results[1]["totals"]["amount"] == 20000
        assert results[2]["date"] == "2026-02-04"
        assert results[2]["totals"]["amount"] == 30000

    def test_reconciliation_range_max_90_days(self, owner):
        """Test that range request over 90 days raises ValueError."""
        with pytest.raises(ValueError, match="90 days"):
            get_reconciliation_range(
                owner.restaurant,
                date(2026, 1, 1),
                date(2026, 4, 15),  # 104 days
            )


@pytest.mark.django_db
class TestReconciliationAPI:
    """Tests for reconciliation API endpoint."""

    def test_reconciliation_api_requires_auth(self, api_client):
        """Test that reconciliation endpoint requires authentication."""
        response = api_client.get("/api/v1/payments/reconciliation/")
        assert response.status_code == 401

    def test_reconciliation_api_requires_manager(self, cashier_client):
        """Test that reconciliation requires manager or owner role."""
        response = cashier_client.get("/api/v1/payments/reconciliation/")
        assert response.status_code == 403

    def test_reconciliation_api_owner_access(self, owner_client, owner):
        """Test that owners can access reconciliation."""
        response = owner_client.get("/api/v1/payments/reconciliation/")
        assert response.status_code == 200
        assert "totals" in response.data
        assert "by_provider" in response.data
        assert "net_amount" in response.data

    def test_reconciliation_api_manager_access(self, manager_client, manager):
        """Test that managers can access reconciliation."""
        response = manager_client.get("/api/v1/payments/reconciliation/")
        assert response.status_code == 200
        assert "totals" in response.data
