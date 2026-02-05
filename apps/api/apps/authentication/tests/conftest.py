import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .factories import (
    CashierFactory,
    ManagerFactory,
    OwnerFactory,
    BusinessFactory,
    UserFactory,
)

# Register factories as pytest fixtures
# This creates both 'business_factory' and 'business' fixtures
register(BusinessFactory)
register(UserFactory)
register(OwnerFactory, "owner")  # Creates 'owner' fixture
register(ManagerFactory, "manager")  # Creates 'manager' fixture
register(CashierFactory, "cashier")  # Creates 'cashier' fixture


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    """Authenticated API client for regular user."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


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
