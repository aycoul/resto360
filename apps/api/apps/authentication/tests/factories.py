import factory
from factory.django import DjangoModelFactory

from apps.authentication.models import Restaurant, User


class RestaurantFactory(DjangoModelFactory):
    """Factory for creating Restaurant instances."""

    class Meta:
        model = Restaurant

    name = factory.Sequence(lambda n: f"Restaurant {n}")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))
    phone = factory.Sequence(lambda n: f"+22507{n:08d}")
    timezone = "Africa/Abidjan"
    currency = "XOF"


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    phone = factory.Sequence(lambda n: f"+22501{n:08d}")
    name = factory.Faker("name")
    role = "cashier"
    restaurant = factory.SubFactory(RestaurantFactory)

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "testpass123")
        if create:
            self.save()


class OwnerFactory(UserFactory):
    """Factory for creating Owner users."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    role = "owner"


class ManagerFactory(UserFactory):
    """Factory for creating Manager users."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    role = "manager"


class CashierFactory(UserFactory):
    """Factory for creating Cashier users."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    role = "cashier"


class KitchenFactory(UserFactory):
    """Factory for creating Kitchen staff users."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    role = "kitchen"


class DriverFactory(UserFactory):
    """Factory for creating Driver users."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    role = "driver"
