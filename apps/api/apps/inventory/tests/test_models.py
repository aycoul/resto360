from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.inventory.models import (
    MovementReason,
    MovementType,
    StockItem,
    StockMovement,
    UnitType,
)

pytestmark = pytest.mark.django_db


class TestStockItemModel:
    """Tests for the StockItem model."""

    def test_create_stock_item(self, owner):
        """Test creating a stock item with all fields."""
        item = StockItem.all_objects.create(
            restaurant=owner.restaurant,
            name="Test Item",
            sku="TEST-001",
            unit=UnitType.KG,
            current_quantity=Decimal("100.0000"),
            low_stock_threshold=Decimal("10.0000"),
            is_active=True,
        )

        assert item.id is not None
        assert item.name == "Test Item"
        assert item.sku == "TEST-001"
        assert item.unit == UnitType.KG
        assert item.current_quantity == Decimal("100.0000")
        assert item.low_stock_threshold == Decimal("10.0000")
        assert item.is_active is True

    def test_stock_item_str_representation(self, stock_item):
        """Test string representation of stock item."""
        expected = f"{stock_item.name} ({stock_item.current_quantity} {stock_item.unit})"
        assert str(stock_item) == expected

    def test_is_low_stock_below_threshold(self, owner):
        """Test is_low_stock when quantity is at or below threshold."""
        item = StockItem.all_objects.create(
            restaurant=owner.restaurant,
            name="Low Stock Item",
            unit=UnitType.PIECE,
            current_quantity=Decimal("5.0000"),
            low_stock_threshold=Decimal("10.0000"),
        )
        assert item.is_low_stock is True

    def test_is_low_stock_above_threshold(self, owner):
        """Test is_low_stock when quantity is above threshold."""
        item = StockItem.all_objects.create(
            restaurant=owner.restaurant,
            name="Normal Stock Item",
            unit=UnitType.PIECE,
            current_quantity=Decimal("50.0000"),
            low_stock_threshold=Decimal("10.0000"),
        )
        assert item.is_low_stock is False

    def test_is_low_stock_no_threshold(self, owner):
        """Test is_low_stock when no threshold is set."""
        item = StockItem.all_objects.create(
            restaurant=owner.restaurant,
            name="No Threshold Item",
            unit=UnitType.PIECE,
            current_quantity=Decimal("0.0000"),
            low_stock_threshold=None,
        )
        assert item.is_low_stock is False

    def test_non_negative_quantity_constraint(self, owner):
        """Test that negative quantities are rejected."""
        with pytest.raises(IntegrityError):
            StockItem.all_objects.create(
                restaurant=owner.restaurant,
                name="Negative Item",
                unit=UnitType.PIECE,
                current_quantity=Decimal("-1.0000"),
            )

    def test_unique_sku_per_restaurant(self, owner):
        """Test that SKU must be unique per restaurant."""
        StockItem.all_objects.create(
            restaurant=owner.restaurant,
            name="Item 1",
            sku="UNIQUE-SKU",
            unit=UnitType.PIECE,
        )

        with pytest.raises(IntegrityError):
            StockItem.all_objects.create(
                restaurant=owner.restaurant,
                name="Item 2",
                sku="UNIQUE-SKU",
                unit=UnitType.PIECE,
            )

    def test_empty_sku_allowed_multiple_times(self, owner):
        """Test that empty SKU can be used multiple times."""
        item1 = StockItem.all_objects.create(
            restaurant=owner.restaurant,
            name="Item 1",
            sku="",
            unit=UnitType.PIECE,
        )
        item2 = StockItem.all_objects.create(
            restaurant=owner.restaurant,
            name="Item 2",
            sku="",
            unit=UnitType.PIECE,
        )

        assert item1.id != item2.id
        assert item1.sku == item2.sku == ""

    def test_same_sku_different_restaurants(self, owner):
        """Test that same SKU can be used in different restaurants."""
        from apps.authentication.tests.factories import RestaurantFactory

        other_restaurant = RestaurantFactory()
        item1 = StockItem.all_objects.create(
            restaurant=owner.restaurant,
            name="Item 1",
            sku="SHARED-SKU",
            unit=UnitType.PIECE,
        )
        item2 = StockItem.all_objects.create(
            restaurant=other_restaurant,
            name="Item 2",
            sku="SHARED-SKU",
            unit=UnitType.PIECE,
        )

        assert item1.sku == item2.sku
        assert item1.restaurant != item2.restaurant

    def test_history_tracking(self, stock_item):
        """Test that django-simple-history tracks changes."""
        original_name = stock_item.name
        stock_item.name = "Updated Name"
        stock_item.save()

        # Check history records exist
        history = stock_item.history.all()
        assert history.count() >= 1

        # The most recent history entry should have the new name
        latest = history.first()
        assert latest.name == "Updated Name"


class TestStockMovementModel:
    """Tests for the StockMovement model."""

    def test_create_stock_movement(self, stock_item, owner):
        """Test creating a stock movement record."""
        movement = StockMovement.all_objects.create(
            restaurant=stock_item.restaurant,
            stock_item=stock_item,
            quantity_change=Decimal("10.0000"),
            movement_type=MovementType.IN,
            reason=MovementReason.PURCHASE,
            notes="Test purchase",
            balance_after=Decimal("110.0000"),
            created_by=owner,
        )

        assert movement.id is not None
        assert movement.stock_item == stock_item
        assert movement.quantity_change == Decimal("10.0000")
        assert movement.movement_type == MovementType.IN
        assert movement.reason == MovementReason.PURCHASE
        assert movement.balance_after == Decimal("110.0000")
        assert movement.created_by == owner

    def test_stock_movement_str_representation(self, stock_item, owner):
        """Test string representation of stock movement."""
        movement = StockMovement.all_objects.create(
            restaurant=stock_item.restaurant,
            stock_item=stock_item,
            quantity_change=Decimal("10.0000"),
            movement_type=MovementType.IN,
            reason=MovementReason.PURCHASE,
            notes="Test purchase",
            balance_after=Decimal("110.0000"),
            created_by=owner,
        )
        expected = (
            f"{movement.stock_item.name}: "
            f"{movement.quantity_change:+} "
            f"({movement.reason})"
        )
        assert str(movement) == expected

    def test_stock_movement_immutability(self, stock_item, owner):
        """Test that existing movements cannot be updated."""
        movement = StockMovement.all_objects.create(
            restaurant=stock_item.restaurant,
            stock_item=stock_item,
            quantity_change=Decimal("10.0000"),
            movement_type=MovementType.IN,
            reason=MovementReason.PURCHASE,
            notes="Initial notes",
            balance_after=Decimal("110.0000"),
            created_by=owner,
        )

        movement.notes = "Trying to update"

        with pytest.raises(ValueError) as exc_info:
            movement.save()

        assert "immutable" in str(exc_info.value).lower()

    def test_stock_movement_ordering(self, stock_item, owner):
        """Test that movements are ordered by -created_at."""
        from datetime import timedelta
        from django.utils import timezone

        # Create movements with explicit timestamps
        older_time = timezone.now() - timedelta(minutes=5)
        movement1 = StockMovement.all_objects.create(
            restaurant=stock_item.restaurant,
            stock_item=stock_item,
            quantity_change=Decimal("5.0000"),
            movement_type=MovementType.IN,
            reason=MovementReason.PURCHASE,
            balance_after=Decimal("105.0000"),
            created_by=owner,
        )
        # Update created_at to be older
        StockMovement.all_objects.filter(pk=movement1.pk).update(created_at=older_time)
        movement1.refresh_from_db()

        movement2 = StockMovement.all_objects.create(
            restaurant=stock_item.restaurant,
            stock_item=stock_item,
            quantity_change=Decimal("-3.0000"),
            movement_type=MovementType.OUT,
            reason=MovementReason.ORDER_USAGE,
            balance_after=Decimal("102.0000"),
            created_by=owner,
        )

        movements = list(StockMovement.all_objects.filter(stock_item=stock_item).order_by("-created_at"))
        # Most recent should be first
        assert movements[0] == movement2
        assert movements[1] == movement1

    def test_movement_reference_fields(self, stock_item, owner):
        """Test movement with reference fields (e.g., linked to an order)."""
        import uuid

        order_id = uuid.uuid4()
        movement = StockMovement.all_objects.create(
            restaurant=stock_item.restaurant,
            stock_item=stock_item,
            quantity_change=Decimal("-2.0000"),
            movement_type=MovementType.OUT,
            reason=MovementReason.ORDER_USAGE,
            reference_type="Order",
            reference_id=order_id,
            balance_after=Decimal("98.0000"),
            created_by=owner,
        )

        assert movement.reference_type == "Order"
        assert movement.reference_id == order_id
