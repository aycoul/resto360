"""Tests for inventory services including order ingredient deduction."""

import pytest
from decimal import Decimal

from apps.inventory.models import StockMovement
from apps.inventory.services import deduct_ingredients_for_order


@pytest.mark.django_db
class TestDeductIngredientsForOrder:
    """Test automatic ingredient deduction for orders."""

    def test_deducts_ingredients_for_order(self, order_with_ingredients):
        """Deduction reduces stock by (quantity_required * order_quantity)."""
        stock_item = order_with_ingredients.stock_item
        initial_qty = stock_item.current_quantity

        # Expected deduction: 0.5 (per unit) * 2 (order quantity) = 1.0
        deduct_ingredients_for_order(order_with_ingredients.order)

        stock_item.refresh_from_db()
        expected = initial_qty - Decimal("1.0")
        assert stock_item.current_quantity == expected

    def test_creates_stock_movement_record(self, order_with_ingredients):
        """Deduction creates StockMovement with order reference."""
        order = order_with_ingredients.order
        stock_item = order_with_ingredients.stock_item

        # No movements initially
        assert not StockMovement.all_objects.filter(
            stock_item=stock_item, reference_type="Order"
        ).exists()

        deduct_ingredients_for_order(order)

        # Should have a movement now
        movement = StockMovement.all_objects.get(
            stock_item=stock_item, reference_type="Order"
        )
        assert movement.reference_id == order.id
        assert movement.reason == "order_usage"
        assert movement.quantity_change == Decimal("-1.0")
        assert f"Order #{order.order_number}" in movement.notes

    def test_logs_warning_for_insufficient_stock(
        self, order_with_insufficient_stock, caplog
    ):
        """Insufficient stock logs warning but continues processing."""
        import logging

        caplog.set_level(logging.WARNING)

        order = order_with_insufficient_stock.order
        deduct_ingredients_for_order(order)

        # Should log warning about insufficient stock
        assert "Insufficient stock" in caplog.text
        assert "manual inventory adjustment required" in caplog.text

    def test_insufficient_stock_does_not_create_movement(
        self, order_with_insufficient_stock
    ):
        """Insufficient stock skips movement (respects non-negative constraint)."""
        order = order_with_insufficient_stock.order
        stock_item = order_with_insufficient_stock.stock_item
        initial_qty = stock_item.current_quantity

        deduct_ingredients_for_order(order)

        # Should NOT have created a movement (would violate non-negative constraint)
        movements = StockMovement.all_objects.filter(
            stock_item=stock_item, reference_type="Order"
        )
        assert not movements.exists()

        # Stock should remain unchanged
        stock_item.refresh_from_db()
        assert stock_item.current_quantity == initial_qty

    def test_skips_menu_items_without_ingredients(self, order_without_ingredients):
        """Orders with no ingredient mappings complete without error."""
        # Should not raise any exceptions
        deduct_ingredients_for_order(order_without_ingredients)

        # No movements should be created
        movements = StockMovement.all_objects.filter(
            reference_type="Order", reference_id=order_without_ingredients.id
        )
        assert not movements.exists()

    def test_handles_deleted_menu_item(self, order_with_ingredients):
        """Order items with deleted menu_item are skipped gracefully."""
        order_item = order_with_ingredients.order_item

        # Simulate menu item being deleted (nullified FK)
        order_item.menu_item = None
        order_item.save()

        # Should not raise any exceptions
        deduct_ingredients_for_order(order_with_ingredients.order)

    def test_deducts_multiple_ingredients(self, owner, db):
        """Order item with multiple ingredients deducts all."""
        from apps.menu.tests.factories import CategoryFactory, MenuItemFactory
        from apps.orders.tests.factories import OrderFactory, OrderItemFactory

        from .factories import MenuItemIngredientFactory, StockItemFactory

        restaurant = owner.restaurant

        # Create two stock items
        tomatoes = StockItemFactory(
            restaurant=restaurant,
            name="Tomatoes",
            current_quantity=Decimal("50.0000"),
        )
        onions = StockItemFactory(
            restaurant=restaurant,
            name="Onions",
            current_quantity=Decimal("30.0000"),
        )

        # Create menu item with multiple ingredients
        category = CategoryFactory(restaurant=restaurant)
        burger = MenuItemFactory(restaurant=restaurant, category=category, name="Burger")

        MenuItemIngredientFactory(
            restaurant=restaurant,
            menu_item=burger,
            stock_item=tomatoes,
            quantity_required=Decimal("0.1"),  # 0.1 kg tomatoes per burger
        )
        MenuItemIngredientFactory(
            restaurant=restaurant,
            menu_item=burger,
            stock_item=onions,
            quantity_required=Decimal("0.05"),  # 0.05 kg onions per burger
        )

        # Create order for 3 burgers
        order = OrderFactory(restaurant=restaurant, cashier=owner)
        OrderItemFactory(
            restaurant=restaurant,
            order=order,
            menu_item=burger,
            quantity=3,
        )

        deduct_ingredients_for_order(order)

        tomatoes.refresh_from_db()
        onions.refresh_from_db()

        # 3 burgers * 0.1 kg = 0.3 kg tomatoes deducted
        assert tomatoes.current_quantity == Decimal("50.0000") - Decimal("0.3")
        # 3 burgers * 0.05 kg = 0.15 kg onions deducted
        assert onions.current_quantity == Decimal("30.0000") - Decimal("0.15")
