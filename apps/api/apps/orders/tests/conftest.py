"""Pytest fixtures for orders app tests."""

import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.tests.factories import (
    CashierFactory,
    KitchenFactory,
    ManagerFactory,
    OwnerFactory,
    RestaurantFactory,
    UserFactory,
)
from apps.menu.tests.factories import (
    CategoryFactory,
    MenuItemFactory,
    ModifierFactory,
    ModifierOptionFactory,
)

from .factories import (
    DailySequenceFactory,
    OrderFactory,
    OrderItemFactory,
    OrderItemModifierFactory,
    TableFactory,
)

# Register authentication factories
register(RestaurantFactory)
register(UserFactory)  # Base user factory for subfactory resolution
register(OwnerFactory, "owner")
register(ManagerFactory, "manager")
register(CashierFactory, "cashier")
register(KitchenFactory, "kitchen_user")

# Register menu factories
register(CategoryFactory)
register(MenuItemFactory)
register(ModifierFactory)
register(ModifierOptionFactory)

# Register order factories
register(TableFactory)
register(DailySequenceFactory)
register(OrderFactory)
register(OrderItemFactory)
register(OrderItemModifierFactory)


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
def kitchen_client(api_client, kitchen_user):
    """Authenticated API client for kitchen staff."""
    refresh = RefreshToken.for_user(kitchen_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def sample_order_data(owner):
    """Create sample menu items and return data for order creation."""
    restaurant = owner.restaurant

    # Create a table
    table = TableFactory(restaurant=restaurant, number="1")

    # Create category and menu items
    category = CategoryFactory(restaurant=restaurant, name="Food")
    burger = MenuItemFactory(
        restaurant=restaurant,
        category=category,
        name="Burger",
        price=5000,
    )
    fries = MenuItemFactory(
        restaurant=restaurant,
        category=category,
        name="Fries",
        price=2000,
    )

    # Create modifier for burger
    size_modifier = ModifierFactory(
        restaurant=restaurant,
        menu_item=burger,
        name="Size",
        required=True,
    )
    large_option = ModifierOptionFactory(
        restaurant=restaurant,
        modifier=size_modifier,
        name="Large",
        price_adjustment=500,
    )

    return {
        "restaurant": restaurant,
        "table": table,
        "burger": burger,
        "fries": fries,
        "size_modifier": size_modifier,
        "large_option": large_option,
    }
