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

from .factories import (
    CategoryFactory,
    MenuItemFactory,
    ModifierFactory,
    ModifierOptionFactory,
)

# Register authentication factories
register(RestaurantFactory)
register(OwnerFactory, "owner")
register(ManagerFactory, "manager")
register(CashierFactory, "cashier")

# Register menu factories
register(CategoryFactory)
register(MenuItemFactory)
register(ModifierFactory)
register(ModifierOptionFactory)


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
def sample_menu(owner):
    """Create a sample menu structure for testing."""
    restaurant = owner.restaurant

    # Create categories
    entrees = CategoryFactory(restaurant=restaurant, name="Entrees", display_order=1)
    drinks = CategoryFactory(restaurant=restaurant, name="Drinks", display_order=2)
    desserts = CategoryFactory(
        restaurant=restaurant, name="Desserts", display_order=3, is_visible=False
    )

    # Create menu items
    burger = MenuItemFactory(
        restaurant=restaurant,
        category=entrees,
        name="Burger",
        price=5000,
    )
    fries = MenuItemFactory(
        restaurant=restaurant,
        category=entrees,
        name="Fries",
        price=2000,
    )
    cola = MenuItemFactory(
        restaurant=restaurant,
        category=drinks,
        name="Cola",
        price=1000,
    )
    unavailable_item = MenuItemFactory(
        restaurant=restaurant,
        category=entrees,
        name="Unavailable Item",
        price=3000,
        is_available=False,
    )

    # Create modifier for burger (Size)
    size_modifier = ModifierFactory(
        restaurant=restaurant,
        menu_item=burger,
        name="Size",
        required=True,
        max_selections=1,
    )
    ModifierOptionFactory(
        restaurant=restaurant,
        modifier=size_modifier,
        name="Small",
        price_adjustment=-500,
    )
    ModifierOptionFactory(
        restaurant=restaurant,
        modifier=size_modifier,
        name="Medium",
        price_adjustment=0,
    )
    ModifierOptionFactory(
        restaurant=restaurant,
        modifier=size_modifier,
        name="Large",
        price_adjustment=500,
    )

    # Create modifier for burger (Extras)
    extras_modifier = ModifierFactory(
        restaurant=restaurant,
        menu_item=burger,
        name="Extras",
        required=False,
        max_selections=0,  # Unlimited
    )
    ModifierOptionFactory(
        restaurant=restaurant,
        modifier=extras_modifier,
        name="Cheese",
        price_adjustment=300,
    )
    ModifierOptionFactory(
        restaurant=restaurant,
        modifier=extras_modifier,
        name="Bacon",
        price_adjustment=500,
    )

    return {
        "restaurant": restaurant,
        "categories": {"entrees": entrees, "drinks": drinks, "desserts": desserts},
        "items": {
            "burger": burger,
            "fries": fries,
            "cola": cola,
            "unavailable": unavailable_item,
        },
        "modifiers": {"size": size_modifier, "extras": extras_modifier},
    }
