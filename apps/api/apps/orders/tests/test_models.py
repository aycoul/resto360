"""Tests for order models."""

import pytest
from django.utils import timezone

from apps.core.context import set_current_restaurant
from apps.orders.models import (
    DailySequence,
    Order,
    OrderItem,
    OrderItemModifier,
    OrderStatus,
    OrderType,
    Table,
)


@pytest.mark.django_db
class TestTableModel:
    """Tests for the Table model."""

    def test_create_table(self, business):
        """Test creating a table."""
        table = Table.all_objects.create(
            business=business,
            number="1",
            capacity=4,
        )
        assert table.number == "1"
        assert table.capacity == 4
        assert table.is_active is True
        assert str(table) == "Table 1"

    def test_table_unique_per_business(self, business):
        """Test table number is unique per business."""
        Table.all_objects.create(business=business, number="1")
        with pytest.raises(Exception):  # IntegrityError
            Table.all_objects.create(business=business, number="1")

    def test_table_tenant_isolation(self, business_factory):
        """Test tables are isolated by business."""
        business_a = business_factory()
        business_b = business_factory()

        Table.all_objects.create(business=business_a, number="1")
        Table.all_objects.create(business=business_b, number="1")

        set_current_restaurant(business_a)
        tables_a = Table.objects.all()
        assert tables_a.count() == 1

        set_current_restaurant(business_b)
        tables_b = Table.objects.all()
        assert tables_b.count() == 1


@pytest.mark.django_db
class TestDailySequenceModel:
    """Tests for the DailySequence model."""

    def test_create_daily_sequence(self, business):
        """Test creating a daily sequence."""
        today = timezone.localdate()
        sequence = DailySequence.objects.create(
            business=business,
            date=today,
            last_number=5,
        )
        assert sequence.date == today
        assert sequence.last_number == 5

    def test_daily_sequence_unique_per_business_per_day(self, business):
        """Test only one sequence per business per day."""
        today = timezone.localdate()
        DailySequence.objects.create(business=business, date=today)
        with pytest.raises(Exception):  # IntegrityError
            DailySequence.objects.create(business=business, date=today)


@pytest.mark.django_db
class TestOrderModel:
    """Tests for the Order model."""

    def test_create_order(self, business, cashier, table_factory):
        """Test creating an order."""
        table = table_factory(business=business)
        order = Order.all_objects.create(
            business=business,
            order_number=1,
            order_type=OrderType.DINE_IN,
            status=OrderStatus.PENDING,
            table=table,
            cashier=cashier,
        )
        assert order.order_number == 1
        assert order.order_type == OrderType.DINE_IN
        assert order.status == OrderStatus.PENDING
        assert str(order) == "Order #1"

    def test_order_type_choices(self):
        """Test OrderType enum values."""
        assert OrderType.DINE_IN == "dine_in"
        assert OrderType.TAKEAWAY == "takeaway"
        assert OrderType.DELIVERY == "delivery"

    def test_order_status_choices(self):
        """Test OrderStatus enum values."""
        assert OrderStatus.PENDING == "pending"
        assert OrderStatus.PREPARING == "preparing"
        assert OrderStatus.READY == "ready"
        assert OrderStatus.COMPLETED == "completed"
        assert OrderStatus.CANCELLED == "cancelled"

    def test_order_sets_completed_at(self, order_factory):
        """Test completed_at is set when status changes to completed."""
        order = order_factory(status=OrderStatus.PENDING)
        assert order.completed_at is None

        order.status = OrderStatus.COMPLETED
        order.save()
        assert order.completed_at is not None

    def test_order_sets_cancelled_at(self, order_factory):
        """Test cancelled_at is set when status changes to cancelled."""
        order = order_factory(status=OrderStatus.PENDING)
        assert order.cancelled_at is None

        order.status = OrderStatus.CANCELLED
        order.cancelled_reason = "Customer changed mind"
        order.save()
        assert order.cancelled_at is not None

    def test_order_tenant_isolation(self, business_factory, cashier_factory):
        """Test orders are isolated by business."""
        business_a = business_factory()
        business_b = business_factory()
        cashier_a = cashier_factory(business=business_a)
        cashier_b = cashier_factory(business=business_b)

        Order.all_objects.create(
            business=business_a,
            order_number=1,
            cashier=cashier_a,
        )
        Order.all_objects.create(
            business=business_b,
            order_number=1,
            cashier=cashier_b,
        )

        set_current_restaurant(business_a)
        orders_a = Order.objects.all()
        assert orders_a.count() == 1

        set_current_restaurant(business_b)
        orders_b = Order.objects.all()
        assert orders_b.count() == 1

    def test_calculate_totals(self, order_factory, order_item_factory):
        """Test order total calculation."""
        order = order_factory(subtotal=0, total=0)
        # Note: line_total is recalculated as unit_price * quantity on save for new items
        # Modifiers are added after item creation in the real flow
        order_item_factory(
            order=order,
            business=order.business,
            unit_price=5000,
            quantity=2,
        )
        order_item_factory(
            order=order,
            business=order.business,
            unit_price=2000,
            quantity=1,
        )

        order.calculate_totals()
        assert order.subtotal == 12000  # (5000 * 2) + (2000 * 1)
        assert order.total == 12000  # No discount


@pytest.mark.django_db
class TestOrderItemModel:
    """Tests for the OrderItem model."""

    def test_create_order_item(self, order_factory, menu_item_factory, category_factory):
        """Test creating an order item."""
        order = order_factory()
        category = category_factory(business=order.business)
        menu_item = menu_item_factory(business=order.business, category=category)

        item = OrderItem.all_objects.create(
            business=order.business,
            order=order,
            menu_item=menu_item,
            name=menu_item.name,
            unit_price=menu_item.price,
            quantity=2,
        )
        assert item.quantity == 2
        assert item.line_total == menu_item.price * 2
        assert str(item) == f"2x {menu_item.name}"

    def test_order_item_cascade_delete(self, order_factory, order_item_factory):
        """Test deleting order cascades to items."""
        order = order_factory()
        item = order_item_factory(order=order, business=order.business)
        item_id = item.id

        assert OrderItem.all_objects.filter(id=item_id).exists()

        order.delete()
        assert not OrderItem.all_objects.filter(id=item_id).exists()


@pytest.mark.django_db
class TestOrderItemModifierModel:
    """Tests for the OrderItemModifier model."""

    def test_create_order_item_modifier(
        self, order_item_factory, modifier_option_factory, modifier_factory, menu_item_factory, category_factory
    ):
        """Test creating an order item modifier."""
        order_item = order_item_factory()
        category = category_factory(business=order_item.business)
        menu_item = menu_item_factory(business=order_item.business, category=category)
        modifier = modifier_factory(business=order_item.business, menu_item=menu_item)
        mod_option = modifier_option_factory(
            business=order_item.business,
            modifier=modifier,
            name="Large",
            price_adjustment=500,
        )

        order_mod = OrderItemModifier.all_objects.create(
            business=order_item.business,
            order_item=order_item,
            modifier_option=mod_option,
            name="Large",
            price_adjustment=500,
        )
        assert order_mod.name == "Large"
        assert order_mod.price_adjustment == 500
        assert str(order_mod) == "Large"

    def test_order_item_modifier_cascade_delete(
        self, order_item_factory, order_item_modifier_factory
    ):
        """Test deleting order item cascades to modifiers."""
        order_item = order_item_factory()
        mod = order_item_modifier_factory(order_item=order_item, business=order_item.business)
        mod_id = mod.id

        assert OrderItemModifier.all_objects.filter(id=mod_id).exists()

        order_item.delete()
        assert not OrderItemModifier.all_objects.filter(id=mod_id).exists()
