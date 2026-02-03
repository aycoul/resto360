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

from apps.menu.tests.factories import CategoryFactory, MenuItemFactory
from apps.orders.tests.factories import OrderFactory, OrderItemFactory

from .factories import MenuItemIngredientFactory, StockItemFactory, StockMovementFactory

# Register authentication factories
register(RestaurantFactory)
register(OwnerFactory, "owner")
register(ManagerFactory, "manager")
register(CashierFactory, "cashier")

# Register inventory factories
register(StockItemFactory)
register(StockMovementFactory)
register(MenuItemIngredientFactory)

# Register menu factories (needed for recipe tests)
register(CategoryFactory)
register(MenuItemFactory)

# Register order factories (needed for signal tests)
register(OrderFactory)
register(OrderItemFactory)


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


@pytest.fixture
def order_with_ingredients(owner, db):
    """Create an order with menu items that have ingredient mappings."""
    from decimal import Decimal

    from apps.orders.models import OrderStatus

    restaurant = owner.restaurant

    # Create stock item with enough quantity
    stock_item = StockItemFactory(
        restaurant=restaurant,
        name="Test Ingredient",
        current_quantity=Decimal("100.0000"),
        low_stock_threshold=Decimal("10.0000"),
    )

    # Create a menu item
    category = CategoryFactory(restaurant=restaurant, name="Test Category")
    menu_item = MenuItemFactory(
        restaurant=restaurant,
        category=category,
        name="Test Menu Item",
        price=1500,
    )

    # Create ingredient mapping: 0.5 kg per menu item
    ingredient = MenuItemIngredientFactory(
        restaurant=restaurant,
        menu_item=menu_item,
        stock_item=stock_item,
        quantity_required=Decimal("0.5000"),
    )

    # Create order with the menu item (quantity 2 = 1.0 kg needed)
    order = OrderFactory(
        restaurant=restaurant,
        cashier=owner,
        status=OrderStatus.PENDING,
    )
    order_item = OrderItemFactory(
        restaurant=restaurant,
        order=order,
        menu_item=menu_item,
        name=menu_item.name,
        unit_price=menu_item.price,
        quantity=2,
        line_total=menu_item.price * 2,
    )

    class Result:
        pass

    result = Result()
    result.order = order
    result.order_item = order_item
    result.menu_item = menu_item
    result.stock_item = stock_item
    result.ingredient = ingredient
    result.owner = owner
    return result


@pytest.fixture
def order_with_insufficient_stock(owner, db):
    """Create an order where stock is insufficient for ingredients."""
    from decimal import Decimal

    from apps.orders.models import OrderStatus

    restaurant = owner.restaurant

    # Create stock item with very low quantity
    stock_item = StockItemFactory(
        restaurant=restaurant,
        name="Low Stock Ingredient",
        current_quantity=Decimal("0.1000"),  # Very low
        low_stock_threshold=Decimal("1.0000"),
    )

    # Create a menu item
    category = CategoryFactory(restaurant=restaurant, name="Test Category 2")
    menu_item = MenuItemFactory(
        restaurant=restaurant,
        category=category,
        name="Test Menu Item 2",
        price=2000,
    )

    # Create ingredient mapping: 1.0 kg per menu item (more than available)
    MenuItemIngredientFactory(
        restaurant=restaurant,
        menu_item=menu_item,
        stock_item=stock_item,
        quantity_required=Decimal("1.0000"),
    )

    # Create order (quantity 1 = 1.0 kg needed, but only 0.1 available)
    order = OrderFactory(
        restaurant=restaurant,
        cashier=owner,
        status=OrderStatus.PENDING,
    )
    OrderItemFactory(
        restaurant=restaurant,
        order=order,
        menu_item=menu_item,
        name=menu_item.name,
        unit_price=menu_item.price,
        quantity=1,
        line_total=menu_item.price,
    )

    class Result:
        pass

    result = Result()
    result.order = order
    result.stock_item = stock_item
    return result


@pytest.fixture
def order_without_ingredients(owner, db):
    """Create an order with menu items that have NO ingredient mappings."""
    from apps.orders.models import OrderStatus

    restaurant = owner.restaurant

    # Create a menu item without any ingredient mappings
    category = CategoryFactory(restaurant=restaurant, name="Test Category 3")
    menu_item = MenuItemFactory(
        restaurant=restaurant,
        category=category,
        name="No Ingredients Item",
        price=1000,
    )

    # Create order
    order = OrderFactory(
        restaurant=restaurant,
        cashier=owner,
        status=OrderStatus.PENDING,
    )
    OrderItemFactory(
        restaurant=restaurant,
        order=order,
        menu_item=menu_item,
        name=menu_item.name,
        unit_price=menu_item.price,
        quantity=1,
        line_total=menu_item.price,
    )

    return order


@pytest.fixture
def completed_order_with_ingredients(order_with_ingredients, db):
    """Create an already-completed order with ingredients (movements exist)."""
    from apps.inventory.services import deduct_ingredients_for_order
    from apps.orders.models import OrderStatus
    from django.utils import timezone

    order = order_with_ingredients.order
    order.status = OrderStatus.COMPLETED
    order.completed_at = timezone.now()
    order.save()

    # Manually process the deduction to simulate already completed
    deduct_ingredients_for_order(order)

    return order_with_ingredients
