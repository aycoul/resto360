import factory
from factory.django import DjangoModelFactory

from apps.authentication.tests.factories import RestaurantFactory
from apps.menu.models import Category, MenuItem, Modifier, ModifierOption


class CategoryFactory(DjangoModelFactory):
    """Factory for creating Category instances."""

    class Meta:
        model = Category

    restaurant = factory.SubFactory(RestaurantFactory)
    name = factory.Sequence(lambda n: f"Category {n}")
    display_order = factory.Sequence(lambda n: n)
    is_visible = True


class MenuItemFactory(DjangoModelFactory):
    """Factory for creating MenuItem instances."""

    class Meta:
        model = MenuItem

    restaurant = factory.LazyAttribute(lambda o: o.category.restaurant)
    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: f"Menu Item {n}")
    description = factory.Faker("sentence")
    price = factory.Faker("random_int", min=500, max=10000, step=100)
    is_available = True


class ModifierFactory(DjangoModelFactory):
    """Factory for creating Modifier instances."""

    class Meta:
        model = Modifier

    restaurant = factory.LazyAttribute(lambda o: o.menu_item.restaurant)
    menu_item = factory.SubFactory(MenuItemFactory)
    name = factory.Sequence(lambda n: f"Modifier {n}")
    required = False
    max_selections = 1
    display_order = factory.Sequence(lambda n: n)


class ModifierOptionFactory(DjangoModelFactory):
    """Factory for creating ModifierOption instances."""

    class Meta:
        model = ModifierOption

    restaurant = factory.LazyAttribute(lambda o: o.modifier.restaurant)
    modifier = factory.SubFactory(ModifierFactory)
    name = factory.Sequence(lambda n: f"Option {n}")
    price_adjustment = 0
    is_available = True
    display_order = factory.Sequence(lambda n: n)
