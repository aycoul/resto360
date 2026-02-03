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

from .factories import StockItemFactory, StockMovementFactory

# Register authentication factories
register(RestaurantFactory)
register(OwnerFactory, "owner")
register(ManagerFactory, "manager")
register(CashierFactory, "cashier")

# Register inventory factories
register(StockItemFactory)
register(StockMovementFactory)


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
def sample_stock_item(owner):
    """Create a sample stock item for the owner's restaurant."""
    return StockItemFactory(
        restaurant=owner.restaurant,
        name="Tomatoes",
        sku="TOM-001",
        unit="kg",
        current_quantity="50.0000",
        low_stock_threshold="5.0000",
    )


@pytest.fixture
def sample_inventory(owner):
    """Create a sample inventory with multiple items."""
    restaurant = owner.restaurant

    items = {
        "tomatoes": StockItemFactory(
            restaurant=restaurant,
            name="Tomatoes",
            sku="TOM-001",
            unit="kg",
            current_quantity="50.0000",
            low_stock_threshold="5.0000",
        ),
        "onions": StockItemFactory(
            restaurant=restaurant,
            name="Onions",
            sku="ONI-001",
            unit="kg",
            current_quantity="30.0000",
            low_stock_threshold="3.0000",
        ),
        "cooking_oil": StockItemFactory(
            restaurant=restaurant,
            name="Cooking Oil",
            sku="OIL-001",
            unit="L",
            current_quantity="20.0000",
            low_stock_threshold="2.0000",
        ),
        "napkins": StockItemFactory(
            restaurant=restaurant,
            name="Napkins",
            sku="NAP-001",
            unit="piece",
            current_quantity="500.0000",
            low_stock_threshold="50.0000",
        ),
        "inactive_item": StockItemFactory(
            restaurant=restaurant,
            name="Discontinued Item",
            sku="DIS-001",
            unit="piece",
            current_quantity="0.0000",
            is_active=False,
        ),
    }

    return {"restaurant": restaurant, "items": items}
