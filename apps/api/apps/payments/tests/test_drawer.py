"""Tests for CashDrawerSession API."""

import pytest
from django.utils import timezone

from apps.payments.models import CashDrawerSession, Payment, PaymentStatus
from apps.payments.tests.factories import PaymentMethodFactory


@pytest.mark.django_db
class TestCashDrawerSessionAPI:
    """Tests for CashDrawerSession ViewSet."""

    def test_open_drawer_session(self, cashier_client, cashier):
        """Test opening a new cash drawer session."""
        response = cashier_client.post(
            "/api/v1/payments/drawer-sessions/open/",
            {"opening_balance": 50000},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["opening_balance"] == 50000
        assert str(response.data["cashier"]) == str(cashier.id)
        assert response.data["is_open"] is True
        assert response.data["closing_balance"] is None
        assert response.data["variance"] is None

    def test_open_drawer_fails_if_already_open(self, cashier_client, cashier):
        """Test that opening a second drawer session fails."""
        # First session
        response = cashier_client.post(
            "/api/v1/payments/drawer-sessions/open/",
            {"opening_balance": 50000},
            format="json",
        )
        assert response.status_code == 201

        # Second session should fail
        response = cashier_client.post(
            "/api/v1/payments/drawer-sessions/open/",
            {"opening_balance": 25000},
            format="json",
        )

        assert response.status_code == 400
        assert "already have an open" in response.data["detail"]

    def test_get_current_session(self, cashier_client, sample_cash_drawer_session):
        """Test retrieving current open session."""
        response = cashier_client.get("/api/v1/payments/drawer-sessions/current/")

        assert response.status_code == 200
        assert response.data["id"] == str(sample_cash_drawer_session.id)
        assert response.data["is_open"] is True
        assert response.data["opening_balance"] == 50000

    def test_get_current_session_404_if_none(self, cashier_client, cashier):
        """Test that current returns 404 if no open session exists."""
        response = cashier_client.get("/api/v1/payments/drawer-sessions/current/")

        assert response.status_code == 404
        assert "No open" in response.data["detail"]

    def test_close_drawer_session(self, cashier_client, cashier, sample_cash_drawer_session):
        """Test closing a drawer session with correct balance."""
        # Create a cash payment during the session
        payment_method = PaymentMethodFactory(
            restaurant=cashier.restaurant,
            provider_code="cash",
            name="Cash",
        )
        from apps.orders.tests.factories import OrderFactory

        order = OrderFactory(restaurant=cashier.restaurant, cashier=cashier)
        payment = Payment.all_objects.create(
            restaurant=cashier.restaurant,
            order=order,
            payment_method=payment_method,
            amount=10000,
            status=PaymentStatus.PENDING,
            idempotency_key="idem-drawer-test",
            provider_code="cash",
            provider_reference="cash-drawer-test",
        )
        # Complete the payment
        payment.start_processing()
        payment.mark_success()
        payment.save()

        # Close with expected balance: 50000 + 10000 = 60000
        response = cashier_client.post(
            f"/api/v1/payments/drawer-sessions/{sample_cash_drawer_session.id}/close/",
            {"closing_balance": 60000},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["is_open"] is False
        assert response.data["closing_balance"] == 60000
        assert response.data["expected_balance"] == 60000
        assert response.data["variance"] == 0

    def test_close_drawer_calculates_variance(
        self, cashier_client, cashier, sample_cash_drawer_session
    ):
        """Test that variance is calculated correctly."""
        # Create a cash payment during the session
        payment_method = PaymentMethodFactory(
            restaurant=cashier.restaurant,
            provider_code="cash",
            name="Cash Variance Test",
        )
        from apps.orders.tests.factories import OrderFactory

        order = OrderFactory(restaurant=cashier.restaurant, cashier=cashier)
        payment = Payment.all_objects.create(
            restaurant=cashier.restaurant,
            order=order,
            payment_method=payment_method,
            amount=10000,
            status=PaymentStatus.PENDING,
            idempotency_key="idem-variance-test",
            provider_code="cash",
            provider_reference="cash-variance-test",
        )
        payment.start_processing()
        payment.mark_success()
        payment.save()

        # Expected: 50000 + 10000 = 60000
        # Actual: 55000 (short 5000)
        response = cashier_client.post(
            f"/api/v1/payments/drawer-sessions/{sample_cash_drawer_session.id}/close/",
            {"closing_balance": 55000, "variance_notes": "Short by 5000"},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["closing_balance"] == 55000
        assert response.data["expected_balance"] == 60000
        assert response.data["variance"] == -5000
        assert response.data["variance_notes"] == "Short by 5000"

    def test_close_drawer_fails_if_already_closed(self, cashier_client, cashier):
        """Test that closing an already closed session fails."""
        # Create and close a session
        session = CashDrawerSession.all_objects.create(
            restaurant=cashier.restaurant,
            cashier=cashier,
            opening_balance=50000,
        )
        session.close(closing_balance=50000)
        session.save()

        # Try to close again
        response = cashier_client.post(
            f"/api/v1/payments/drawer-sessions/{session.id}/close/",
            {"closing_balance": 50000},
            format="json",
        )

        assert response.status_code == 400
        assert "already closed" in response.data["detail"]

    def test_close_drawer_fails_for_other_user(
        self, cashier_client, owner, sample_cash_drawer_session
    ):
        """Test that closing another user's session fails."""
        # Create session for owner, not cashier
        session = CashDrawerSession.all_objects.create(
            restaurant=owner.restaurant,
            cashier=owner,
            opening_balance=50000,
        )

        # Cashier tries to close owner's session
        response = cashier_client.post(
            f"/api/v1/payments/drawer-sessions/{session.id}/close/",
            {"closing_balance": 50000},
            format="json",
        )

        # Should return 403 or 404 depending on implementation
        assert response.status_code in [403, 404]

    def test_list_drawer_sessions(self, cashier_client, sample_cash_drawer_session):
        """Test listing drawer sessions."""
        response = cashier_client.get("/api/v1/payments/drawer-sessions/")

        assert response.status_code == 200
        # Results may be paginated
        if "results" in response.data:
            assert len(response.data["results"]) >= 1
        else:
            assert len(response.data) >= 1

    def test_retrieve_drawer_session(self, cashier_client, sample_cash_drawer_session):
        """Test retrieving a specific drawer session."""
        response = cashier_client.get(
            f"/api/v1/payments/drawer-sessions/{sample_cash_drawer_session.id}/"
        )

        assert response.status_code == 200
        assert response.data["id"] == str(sample_cash_drawer_session.id)
        assert response.data["opening_balance"] == 50000

    def test_drawer_session_no_delete(self, cashier_client, sample_cash_drawer_session):
        """Test that drawer sessions cannot be deleted."""
        response = cashier_client.delete(
            f"/api/v1/payments/drawer-sessions/{sample_cash_drawer_session.id}/"
        )

        # DELETE should not be allowed
        assert response.status_code == 405  # Method Not Allowed

    def test_drawer_session_no_update(self, cashier_client, sample_cash_drawer_session):
        """Test that drawer sessions cannot be updated directly."""
        response = cashier_client.patch(
            f"/api/v1/payments/drawer-sessions/{sample_cash_drawer_session.id}/",
            {"opening_balance": 100000},
            format="json",
        )

        # PATCH should not be allowed
        assert response.status_code == 405  # Method Not Allowed


@pytest.mark.django_db
class TestPaymentMethodAPI:
    """Tests for PaymentMethod ViewSet."""

    def test_list_payment_methods(self, owner_client, sample_payment_method):
        """Test listing payment methods."""
        response = owner_client.get("/api/v1/payments/methods/")

        assert response.status_code == 200

    def test_create_payment_method(self, owner_client, owner):
        """Test creating a payment method."""
        response = owner_client.post(
            "/api/v1/payments/methods/",
            {
                "provider_code": "wave",
                "name": "Wave Mobile Money",
                "is_active": True,
                "display_order": 1,
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["provider_code"] == "wave"
        assert response.data["name"] == "Wave Mobile Money"

    def test_unauthenticated_access_denied(self, api_client):
        """Test that unauthenticated requests are denied."""
        response = api_client.get("/api/v1/payments/methods/")

        assert response.status_code == 401
