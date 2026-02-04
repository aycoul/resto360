"""Pytest fixtures for payments tests."""

import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.tests.factories import (
    CashierFactory,
    ManagerFactory,
    OwnerFactory,
    RestaurantFactory,
)
from apps.orders.tests.factories import OrderFactory

from .factories import (
    CashDrawerSessionFactory,
    PaymentFactory,
    PaymentMethodFactory,
)

# Register authentication factories
register(RestaurantFactory)
register(OwnerFactory, "owner")
register(ManagerFactory, "manager")
register(CashierFactory, "cashier")

# Register order factories
register(OrderFactory)

# Register payment factories
register(PaymentMethodFactory)
register(PaymentFactory)
register(CashDrawerSessionFactory)


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def owner_client(api_client, owner):
    """Authenticated API client for owner."""
    refresh = RefreshToken.for_user(owner)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def manager_client(api_client, manager):
    """Authenticated API client for manager."""
    refresh = RefreshToken.for_user(manager)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def cashier_client(api_client, cashier):
    """Authenticated API client for cashier."""
    refresh = RefreshToken.for_user(cashier)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def sample_payment_method(owner):
    """Create a sample payment method for the owner's restaurant."""
    return PaymentMethodFactory(
        restaurant=owner.restaurant,
        provider_code="cash",
        name="Cash",
        is_active=True,
    )


@pytest.fixture
def sample_payment(owner, sample_payment_method):
    """Create a sample payment for the owner's restaurant."""
    from apps.orders.tests.factories import OrderFactory

    order = OrderFactory(restaurant=owner.restaurant, cashier=owner)
    return PaymentFactory(
        restaurant=owner.restaurant,
        order=order,
        payment_method=sample_payment_method,
        amount=15000,
    )


@pytest.fixture
def sample_cash_drawer_session(cashier):
    """Create a sample open cash drawer session."""
    return CashDrawerSessionFactory(
        restaurant=cashier.restaurant,
        cashier=cashier,
        opening_balance=50000,
    )
