import pytest

from apps.core.context import set_current_restaurant
from apps.menu.models import Category, MenuItem, Modifier, ModifierOption


@pytest.mark.django_db
class TestCategoryModel:
    """Tests for the Category model."""

    def test_create_category(self, restaurant):
        """Test creating a category with required fields."""
        category = Category.all_objects.create(
            restaurant=restaurant,
            name="Entrees",
            display_order=1,
        )
        assert category.name == "Entrees"
        assert category.display_order == 1
        assert category.is_visible is True
        assert str(category) == "Entrees"

    def test_category_ordering(self, restaurant):
        """Test categories are ordered by display_order then name."""
        Category.all_objects.create(
            restaurant=restaurant, name="Drinks", display_order=2
        )
        Category.all_objects.create(
            restaurant=restaurant, name="Entrees", display_order=1
        )
        Category.all_objects.create(
            restaurant=restaurant, name="Appetizers", display_order=1
        )

        # Set tenant context for TenantManager filtering
        set_current_restaurant(restaurant)
        categories = list(Category.objects.all())

        # display_order 1: Appetizers, Entrees (alphabetically)
        # display_order 2: Drinks
        assert categories[0].name == "Appetizers"
        assert categories[1].name == "Entrees"
        assert categories[2].name == "Drinks"

    def test_category_tenant_isolation(self, restaurant_factory):
        """Test categories are isolated by restaurant."""
        restaurant_a = restaurant_factory()
        restaurant_b = restaurant_factory()

        Category.all_objects.create(restaurant=restaurant_a, name="Category A")
        Category.all_objects.create(restaurant=restaurant_b, name="Category B")

        # Set context to restaurant A
        set_current_restaurant(restaurant_a)
        categories_a = Category.objects.all()
        assert categories_a.count() == 1
        assert categories_a.first().name == "Category A"

        # Set context to restaurant B
        set_current_restaurant(restaurant_b)
        categories_b = Category.objects.all()
        assert categories_b.count() == 1
        assert categories_b.first().name == "Category B"


@pytest.mark.django_db
class TestMenuItemModel:
    """Tests for the MenuItem model."""

    def test_create_menu_item(self, category):
        """Test creating a menu item with required fields."""
        item = MenuItem.all_objects.create(
            restaurant=category.restaurant,
            category=category,
            name="Burger",
            price=5000,
        )
        assert item.name == "Burger"
        assert item.price == 5000
        assert item.is_available is True
        assert str(item) == "Burger"

    def test_menu_item_with_description(self, category):
        """Test menu item with optional description."""
        item = MenuItem.all_objects.create(
            restaurant=category.restaurant,
            category=category,
            name="Burger",
            description="Juicy beef patty with fresh vegetables",
            price=5000,
        )
        assert item.description == "Juicy beef patty with fresh vegetables"

    def test_menu_item_category_relationship(self, category):
        """Test menu item belongs to category."""
        item = MenuItem.all_objects.create(
            restaurant=category.restaurant,
            category=category,
            name="Burger",
            price=5000,
        )
        assert item.category == category
        # Use all_objects for related lookup (not filtered by tenant)
        assert item in category.items.all()

    def test_cascade_delete_on_category(self, category):
        """Test deleting category cascades to items."""
        item = MenuItem.all_objects.create(
            restaurant=category.restaurant,
            category=category,
            name="Burger",
            price=5000,
        )
        item_id = item.id

        # Use all_objects to check without tenant filtering
        assert MenuItem.all_objects.filter(id=item_id).count() == 1

        # Delete category
        category.delete()

        # Item should be deleted (check with all_objects)
        assert MenuItem.all_objects.filter(id=item_id).count() == 0

    def test_menu_item_tenant_isolation(self, category_factory):
        """Test menu items are isolated by restaurant."""
        category_a = category_factory()
        category_b = category_factory()

        MenuItem.all_objects.create(
            restaurant=category_a.restaurant,
            category=category_a,
            name="Item A",
            price=1000,
        )
        MenuItem.all_objects.create(
            restaurant=category_b.restaurant,
            category=category_b,
            name="Item B",
            price=2000,
        )

        # Set context to restaurant A
        set_current_restaurant(category_a.restaurant)
        items_a = MenuItem.objects.all()
        assert items_a.count() == 1
        assert items_a.first().name == "Item A"


@pytest.mark.django_db
class TestModifierModel:
    """Tests for the Modifier model."""

    def test_create_modifier(self, menu_item):
        """Test creating a modifier."""
        modifier = Modifier.all_objects.create(
            restaurant=menu_item.restaurant,
            menu_item=menu_item,
            name="Size",
            required=True,
            max_selections=1,
        )
        assert modifier.name == "Size"
        assert modifier.required is True
        assert modifier.max_selections == 1
        assert str(modifier) == f"{menu_item.name} - Size"

    def test_modifier_menu_item_relationship(self, menu_item):
        """Test modifier belongs to menu item."""
        modifier = Modifier.all_objects.create(
            restaurant=menu_item.restaurant,
            menu_item=menu_item,
            name="Size",
        )
        assert modifier.menu_item == menu_item
        # Use all_objects for related lookup (not filtered by tenant)
        assert modifier in menu_item.modifiers.all()

    def test_cascade_delete_on_menu_item(self, menu_item):
        """Test deleting menu item cascades to modifiers."""
        modifier = Modifier.all_objects.create(
            restaurant=menu_item.restaurant,
            menu_item=menu_item,
            name="Size",
        )
        modifier_id = modifier.id

        assert Modifier.all_objects.filter(id=modifier_id).count() == 1

        menu_item.delete()
        assert Modifier.all_objects.filter(id=modifier_id).count() == 0


@pytest.mark.django_db
class TestModifierOptionModel:
    """Tests for the ModifierOption model."""

    def test_create_modifier_option(self, modifier):
        """Test creating a modifier option."""
        option = ModifierOption.all_objects.create(
            restaurant=modifier.restaurant,
            modifier=modifier,
            name="Large",
            price_adjustment=500,
        )
        assert option.name == "Large"
        assert option.price_adjustment == 500
        assert option.is_available is True
        assert str(option) == f"{modifier.name} - Large"

    def test_modifier_option_negative_price(self, modifier):
        """Test modifier option can have negative price adjustment."""
        option = ModifierOption.all_objects.create(
            restaurant=modifier.restaurant,
            modifier=modifier,
            name="Small",
            price_adjustment=-500,
        )
        assert option.price_adjustment == -500

    def test_modifier_option_relationship(self, modifier):
        """Test modifier option belongs to modifier."""
        option = ModifierOption.all_objects.create(
            restaurant=modifier.restaurant,
            modifier=modifier,
            name="Large",
        )
        assert option.modifier == modifier
        # Use all_objects for related lookup (not filtered by tenant)
        assert option in modifier.options.all()

    def test_cascade_delete_on_modifier(self, modifier):
        """Test deleting modifier cascades to options."""
        option = ModifierOption.all_objects.create(
            restaurant=modifier.restaurant,
            modifier=modifier,
            name="Large",
        )
        option_id = option.id

        assert ModifierOption.all_objects.filter(id=option_id).count() == 1

        modifier.delete()
        assert ModifierOption.all_objects.filter(id=option_id).count() == 0
