"""Factories for creating test instances of order models."""

import factory
from factory.django import DjangoModelFactory

from apps.authentication.tests.factories import RestaurantFactory, CashierFactory
from apps.menu.tests.factories import MenuItemFactory, ModifierOptionFactory

from apps.orders.models import (
    DailySequence,
    Order,
    OrderItem,
    OrderItemModifier,
    OrderStatus,
    OrderType,
    Table,
)


class TableFactory(DjangoModelFactory):
    """Factory for creating Table instances."""

    class Meta:
        model = Table

    restaurant = factory.SubFactory(RestaurantFactory)
    number = factory.Sequence(lambda n: str(n + 1))
    capacity = 4
    is_active = True


class DailySequenceFactory(DjangoModelFactory):
    """Factory for creating DailySequence instances."""

    class Meta:
        model = DailySequence

    restaurant = factory.SubFactory(RestaurantFactory)
    date = factory.Faker("date_object")
    last_number = 0


class OrderFactory(DjangoModelFactory):
    """Factory for creating Order instances."""

    class Meta:
        model = Order

    restaurant = factory.LazyAttribute(lambda o: o.cashier.restaurant if o.cashier else RestaurantFactory())
    order_number = factory.Sequence(lambda n: n + 1)
    order_type = OrderType.DINE_IN
    status = OrderStatus.PENDING
    cashier = factory.SubFactory(CashierFactory)
    table = factory.LazyAttribute(
        lambda o: TableFactory(restaurant=o.restaurant) if o.order_type == OrderType.DINE_IN else None
    )
    customer_name = factory.Faker("name")
    customer_phone = factory.Sequence(lambda n: f"+22507{n:08d}")
    notes = ""
    subtotal = 0
    discount = 0
    total = 0


class OrderItemFactory(DjangoModelFactory):
    """Factory for creating OrderItem instances."""

    class Meta:
        model = OrderItem

    restaurant = factory.LazyAttribute(lambda o: o.order.restaurant)
    order = factory.SubFactory(OrderFactory)
    menu_item = factory.SubFactory(MenuItemFactory)
    name = factory.LazyAttribute(lambda o: o.menu_item.name if o.menu_item else "Item")
    unit_price = factory.LazyAttribute(lambda o: o.menu_item.price if o.menu_item else 1000)
    quantity = 1
    modifiers_total = 0
    line_total = factory.LazyAttribute(lambda o: o.unit_price * o.quantity)
    notes = ""


class OrderItemModifierFactory(DjangoModelFactory):
    """Factory for creating OrderItemModifier instances."""

    class Meta:
        model = OrderItemModifier

    restaurant = factory.LazyAttribute(lambda o: o.order_item.restaurant)
    order_item = factory.SubFactory(OrderItemFactory)
    modifier_option = factory.SubFactory(ModifierOptionFactory)
    name = factory.LazyAttribute(
        lambda o: o.modifier_option.name if o.modifier_option else "Modifier"
    )
    price_adjustment = factory.LazyAttribute(
        lambda o: o.modifier_option.price_adjustment if o.modifier_option else 0
    )
