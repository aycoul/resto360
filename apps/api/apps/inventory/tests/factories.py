from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from apps.authentication.tests.factories import BusinessFactory, OwnerFactory
from apps.inventory.models import (
    MenuItemIngredient,
    MovementReason,
    MovementType,
    StockItem,
    StockMovement,
    UnitType,
)
from apps.menu.tests.factories import ProductFactory


class StockItemFactory(DjangoModelFactory):
    """Factory for creating StockItem instances."""

    class Meta:
        model = StockItem

    business = factory.SubFactory(BusinessFactory)
    name = factory.Sequence(lambda n: f"Stock Item {n}")
    sku = factory.Sequence(lambda n: f"SKU-{n:05d}")
    unit = UnitType.PIECE
    current_quantity = Decimal("100.0000")
    low_stock_threshold = Decimal("10.0000")
    is_active = True


class StockMovementFactory(DjangoModelFactory):
    """Factory for creating StockMovement instances."""

    class Meta:
        model = StockMovement

    business = factory.LazyAttribute(lambda o: o.stock_item.business)
    stock_item = factory.SubFactory(StockItemFactory)
    quantity_change = Decimal("10.0000")
    movement_type = MovementType.IN
    reason = MovementReason.PURCHASE
    notes = factory.Faker("sentence")
    balance_after = Decimal("110.0000")
    created_by = factory.LazyAttribute(
        lambda o: OwnerFactory(business=o.stock_item.business)
    )


class MenuItemIngredientFactory(DjangoModelFactory):
    """Factory for creating MenuItemIngredient instances (recipe mappings)."""

    class Meta:
        model = MenuItemIngredient

    business = factory.LazyAttribute(lambda o: o.stock_item.business)
    menu_item = factory.SubFactory(
        ProductFactory,
        business=factory.LazyAttribute(lambda o: o.factory_parent.business),
    )
    stock_item = factory.SubFactory(StockItemFactory)
    quantity_required = Decimal("0.2500")  # 0.25 units per menu item
