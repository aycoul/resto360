import factory
from factory.django import DjangoModelFactory

from apps.authentication.tests.factories import BusinessFactory
from apps.menu.models import Category, Product, Modifier, ModifierOption


class CategoryFactory(DjangoModelFactory):
    """Factory for creating Category instances."""

    class Meta:
        model = Category

    business = factory.SubFactory(BusinessFactory)
    name = factory.Sequence(lambda n: f"Category {n}")
    display_order = factory.Sequence(lambda n: n)
    is_visible = True


class ProductFactory(DjangoModelFactory):
    """Factory for creating Product instances."""

    class Meta:
        model = Product

    business = factory.LazyAttribute(lambda o: o.category.business)
    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: f"Product {n}")
    description = factory.Faker("sentence")
    price = factory.Faker("random_int", min=500, max=10000, step=100)
    is_available = True


class MenuItemFactory(ProductFactory):
    """Backwards compatible factory (same as ProductFactory)."""

    class Meta:
        model = Product


class ModifierFactory(DjangoModelFactory):
    """Factory for creating Modifier instances."""

    class Meta:
        model = Modifier

    business = factory.LazyAttribute(lambda o: o.menu_item.business)
    menu_item = factory.SubFactory(MenuItemFactory)
    name = factory.Sequence(lambda n: f"Modifier {n}")
    required = False
    max_selections = 1
    display_order = factory.Sequence(lambda n: n)


class ModifierOptionFactory(DjangoModelFactory):
    """Factory for creating ModifierOption instances."""

    class Meta:
        model = ModifierOption

    business = factory.LazyAttribute(lambda o: o.modifier.business)
    modifier = factory.SubFactory(ModifierFactory)
    name = factory.Sequence(lambda n: f"Option {n}")
    price_adjustment = 0
    is_available = True
    display_order = factory.Sequence(lambda n: n)
