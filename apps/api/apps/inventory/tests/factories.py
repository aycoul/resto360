from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from apps.authentication.tests.factories import OwnerFactory, RestaurantFactory
from apps.inventory.models import (
    MovementReason,
    MovementType,
    StockItem,
    StockMovement,
    UnitType,
)


class StockItemFactory(DjangoModelFactory):
    """Factory for creating StockItem instances."""

    class Meta:
        model = StockItem

    restaurant = factory.SubFactory(RestaurantFactory)
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

    restaurant = factory.LazyAttribute(lambda o: o.stock_item.restaurant)
    stock_item = factory.SubFactory(StockItemFactory)
    quantity_change = Decimal("10.0000")
    movement_type = MovementType.IN
    reason = MovementReason.PURCHASE
    notes = factory.Faker("sentence")
    balance_after = Decimal("110.0000")
    created_by = factory.LazyAttribute(
        lambda o: OwnerFactory(restaurant=o.stock_item.restaurant)
    )
