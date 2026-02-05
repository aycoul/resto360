import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.tests.factories import (
    BusinessFactory,
    CashierFactory,
    ManagerFactory,
    OwnerFactory,
)

from .factories import (
    CategoryFactory,
    MenuItemFactory,
    ModifierFactory,
    ModifierOptionFactory,
    ProductFactory,
)

# Register authentication factories
register(BusinessFactory)
register(OwnerFactory, "owner")
register(ManagerFactory, "manager")
register(CashierFactory, "cashier")

# Register menu factories
register(CategoryFactory)
register(ProductFactory)  # Base factory for fixture resolution
register(MenuItemFactory, "menu_item")  # Alias with explicit name
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
    business = owner.business

    # Create categories
    entrees = CategoryFactory(business=business, name="Entrees", display_order=1)
    drinks = CategoryFactory(business=business, name="Drinks", display_order=2)
    desserts = CategoryFactory(
        business=business, name="Desserts", display_order=3, is_visible=False
    )

    # Create menu items
    burger = MenuItemFactory(
        business=business,
        category=entrees,
        name="Burger",
        price=5000,
    )
    fries = MenuItemFactory(
        business=business,
        category=entrees,
        name="Fries",
        price=2000,
    )
    cola = MenuItemFactory(
        business=business,
        category=drinks,
        name="Cola",
        price=1000,
    )
    unavailable_item = MenuItemFactory(
        business=business,
        category=entrees,
        name="Unavailable Item",
        price=3000,
        is_available=False,
    )

    # Create modifier for burger (Size)
    size_modifier = ModifierFactory(
        business=business,
        menu_item=burger,
        name="Size",
        required=True,
        max_selections=1,
    )
    ModifierOptionFactory(
        business=business,
        modifier=size_modifier,
        name="Small",
        price_adjustment=-500,
    )
    ModifierOptionFactory(
        business=business,
        modifier=size_modifier,
        name="Medium",
        price_adjustment=0,
    )
    ModifierOptionFactory(
        business=business,
        modifier=size_modifier,
        name="Large",
        price_adjustment=500,
    )

    # Create modifier for burger (Extras)
    extras_modifier = ModifierFactory(
        business=business,
        menu_item=burger,
        name="Extras",
        required=False,
        max_selections=0,  # Unlimited
    )
    ModifierOptionFactory(
        business=business,
        modifier=extras_modifier,
        name="Cheese",
        price_adjustment=300,
    )
    ModifierOptionFactory(
        business=business,
        modifier=extras_modifier,
        name="Bacon",
        price_adjustment=500,
    )

    return {
        "business": business,
        "categories": {"entrees": entrees, "drinks": drinks, "desserts": desserts},
        "items": {
            "burger": burger,
            "fries": fries,
            "cola": cola,
            "unavailable": unavailable_item,
        },
        "modifiers": {"size": size_modifier, "extras": extras_modifier},
    }
