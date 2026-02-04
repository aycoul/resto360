"""Factories for delivery tests."""

import factory
from django.contrib.gis.geos import Point, Polygon

from apps.authentication.tests.factories import RestaurantFactory, UserFactory
from apps.delivery.models import Delivery, DeliveryZone, Driver


class DeliveryZoneFactory(factory.django.DjangoModelFactory):
    """Factory for DeliveryZone model."""

    class Meta:
        model = DeliveryZone

    restaurant = factory.SubFactory(RestaurantFactory)
    name = factory.Sequence(lambda n: f"Zone {n}")
    polygon = factory.LazyFunction(
        lambda: Polygon(
            [
                (-4.02, 5.32),
                (-4.02, 5.34),
                (-4.00, 5.34),
                (-4.00, 5.32),
                (-4.02, 5.32),
            ],
            srid=4326,
        )
    )
    delivery_fee = 1500
    minimum_order = 5000
    estimated_time_minutes = 30
    is_active = True


class DriverFactory(factory.django.DjangoModelFactory):
    """Factory for Driver model."""

    class Meta:
        model = Driver

    restaurant = factory.SubFactory(RestaurantFactory)
    user = factory.SubFactory(
        UserFactory, role="driver", restaurant=factory.SelfAttribute("..restaurant")
    )
    phone = factory.LazyAttribute(lambda obj: obj.user.phone)
    vehicle_type = "motorcycle"
    vehicle_plate = factory.Sequence(lambda n: f"AB-{n:04d}-CI")
    is_available = False
    current_location = None


class DeliveryFactory(factory.django.DjangoModelFactory):
    """Factory for Delivery model."""

    class Meta:
        model = Delivery

    restaurant = factory.SubFactory(RestaurantFactory)
    order = factory.LazyAttribute(
        lambda obj: _create_order(obj.restaurant)
    )
    zone = factory.SubFactory(
        DeliveryZoneFactory, restaurant=factory.SelfAttribute("..restaurant")
    )
    status = "pending_assignment"
    pickup_address = factory.LazyAttribute(
        lambda obj: obj.restaurant.address or "123 Restaurant St"
    )
    pickup_location = factory.LazyFunction(lambda: Point(-4.01, 5.33, srid=4326))
    delivery_address = "456 Customer Ave, Abidjan"
    delivery_location = factory.LazyFunction(lambda: Point(-4.015, 5.335, srid=4326))
    delivery_fee = 1500
    customer_name = factory.Faker("name")
    customer_phone = factory.Faker("phone_number")


def _create_order(restaurant):
    """Helper to create an order for a delivery."""
    from apps.orders.tests.factories import OrderFactory

    return OrderFactory(
        restaurant=restaurant,
        order_type="delivery",
    )
