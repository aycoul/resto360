"""Tests for payment models."""

import pytest
from django.db import IntegrityError
from django.utils import timezone
from django_fsm import TransitionNotAllowed

from apps.payments.models import (
    CashDrawerSession,
    Payment,
    PaymentMethod,
    PaymentStatus,
)

from .factories import (
    CashDrawerSessionFactory,
    PaymentFactory,
    PaymentMethodFactory,
)


@pytest.mark.django_db
class TestPaymentFSMTransitions:
    """Tests for Payment FSM state transitions."""

    def test_payment_fsm_pending_to_processing(self, sample_payment):
        """Test that payment can transition from PENDING to PROCESSING."""
        assert sample_payment.status == PaymentStatus.PENDING

        sample_payment.start_processing()
        sample_payment.save()

        assert sample_payment.status == PaymentStatus.PROCESSING

    def test_payment_fsm_processing_to_success(self, sample_payment):
        """Test that payment can transition from PROCESSING to SUCCESS."""
        sample_payment.start_processing()
        sample_payment.save()

        assert sample_payment.completed_at is None

        sample_payment.mark_success()
        sample_payment.save()

        assert sample_payment.status == PaymentStatus.SUCCESS
        assert sample_payment.completed_at is not None

    def test_payment_fsm_processing_to_failed(self, sample_payment):
        """Test that payment can transition from PROCESSING to FAILED."""
        sample_payment.start_processing()
        sample_payment.save()

        sample_payment.mark_failed(error_code="DECLINED", error_message="Card declined")
        sample_payment.save()

        assert sample_payment.status == PaymentStatus.FAILED
        assert sample_payment.error_code == "DECLINED"
        assert sample_payment.error_message == "Card declined"
        assert sample_payment.completed_at is not None

    def test_payment_fsm_processing_to_expired(self, sample_payment):
        """Test that payment can transition from PROCESSING to EXPIRED."""
        sample_payment.start_processing()
        sample_payment.save()

        sample_payment.mark_expired()
        sample_payment.save()

        assert sample_payment.status == PaymentStatus.EXPIRED
        assert sample_payment.completed_at is not None

    def test_payment_fsm_success_to_refunded(self, sample_payment):
        """Test that successful payment can be refunded."""
        sample_payment.start_processing()
        sample_payment.mark_success()
        sample_payment.save()

        assert sample_payment.refunded_amount == 0

        sample_payment.mark_refunded()
        sample_payment.save()

        assert sample_payment.status == PaymentStatus.REFUNDED
        assert sample_payment.refunded_amount == sample_payment.amount

    def test_payment_fsm_success_to_partially_refunded(self, sample_payment):
        """Test that successful payment can be partially refunded."""
        sample_payment.start_processing()
        sample_payment.mark_success()
        sample_payment.save()

        partial_amount = sample_payment.amount // 2
        sample_payment.mark_partially_refunded(partial_amount)
        sample_payment.save()

        assert sample_payment.status == PaymentStatus.PARTIALLY_REFUNDED
        assert sample_payment.refunded_amount == partial_amount

    def test_payment_fsm_invalid_transition_pending_to_success(self, sample_payment):
        """Test that invalid transition from PENDING to SUCCESS raises error."""
        assert sample_payment.status == PaymentStatus.PENDING

        with pytest.raises(TransitionNotAllowed):
            sample_payment.mark_success()

    def test_payment_fsm_invalid_transition_pending_to_refunded(self, sample_payment):
        """Test that invalid transition from PENDING to REFUNDED raises error."""
        assert sample_payment.status == PaymentStatus.PENDING

        with pytest.raises(TransitionNotAllowed):
            sample_payment.mark_refunded()


@pytest.mark.django_db
class TestPaymentMethod:
    """Tests for PaymentMethod model."""

    def test_payment_method_unique_per_business(self, owner):
        """Test that same provider_code fails for same business."""
        PaymentMethodFactory(
            business=owner.business,
            provider_code="wave",
            name="Wave",
        )

        with pytest.raises(IntegrityError):
            PaymentMethodFactory(
                business=owner.business,
                provider_code="wave",
                name="Wave Duplicate",
            )

    def test_payment_method_same_code_different_businesses(self, owner):
        """Test that same provider_code works for different businesses."""
        from apps.authentication.tests.factories import BusinessFactory

        # Create a second business
        other_business = BusinessFactory()

        pm1 = PaymentMethodFactory(
            business=owner.business,
            provider_code="wave",
            name="Wave",
        )
        pm2 = PaymentMethodFactory(
            business=other_business,
            provider_code="wave",
            name="Wave",
        )

        assert pm1.provider_code == pm2.provider_code
        assert pm1.business != pm2.business

    def test_payment_method_str(self, sample_payment_method):
        """Test string representation of PaymentMethod."""
        assert str(sample_payment_method) == "Cash (cash)"


@pytest.mark.django_db
class TestCashDrawerSession:
    """Tests for CashDrawerSession model."""

    def test_cash_drawer_is_open_property(self, sample_cash_drawer_session):
        """Test that is_open returns True when closed_at is None."""
        assert sample_cash_drawer_session.closed_at is None
        assert sample_cash_drawer_session.is_open is True

    def test_cash_drawer_is_closed_property(self, sample_cash_drawer_session):
        """Test that is_open returns False when closed_at is set."""
        sample_cash_drawer_session.closed_at = timezone.now()
        sample_cash_drawer_session.save()

        assert sample_cash_drawer_session.is_open is False

    def test_cash_drawer_close_calculates_variance(self, sample_cash_drawer_session):
        """Test that closing calculates expected balance and variance."""
        # Opening balance is 50000
        opening = sample_cash_drawer_session.opening_balance

        # Close with more than opening (profit)
        closing = 65000
        sample_cash_drawer_session.close(closing_balance=closing, notes="Good day")
        sample_cash_drawer_session.save()

        assert sample_cash_drawer_session.is_open is False
        assert sample_cash_drawer_session.closing_balance == closing
        assert sample_cash_drawer_session.expected_balance == opening  # No payments
        assert sample_cash_drawer_session.variance == closing - opening
        assert sample_cash_drawer_session.variance_notes == "Good day"

    def test_cash_drawer_close_with_cash_payments(self, owner, cashier):
        """Test that closing includes successful cash payments in expected."""
        from apps.orders.tests.factories import OrderFactory

        # Create cash drawer session
        session = CashDrawerSessionFactory(
            business=owner.business,
            cashier=cashier,
            opening_balance=50000,
        )

        # Create a cash payment method
        payment_method = PaymentMethodFactory(
            business=owner.business,
            provider_code="cash",
            name="Cash",
        )

        # Create a successful cash payment
        order = OrderFactory(business=owner.business, cashier=owner)
        payment = PaymentFactory(
            business=owner.business,
            order=order,
            payment_method=payment_method,
            amount=10000,
            provider_code="cash",
        )
        payment.start_processing()
        payment.mark_success()
        payment.save()

        # Close the drawer
        actual_closing = 60000
        session.close(closing_balance=actual_closing)
        session.save()

        # Expected = opening + successful cash payments
        expected = 50000 + 10000
        assert session.expected_balance == expected
        assert session.variance == actual_closing - expected

    def test_cash_drawer_str(self, sample_cash_drawer_session):
        """Test string representation of CashDrawerSession."""
        result = str(sample_cash_drawer_session)
        assert "Cash Drawer" in result
        assert "Open" in result
