import pytest

from apps.menu.models import Category


@pytest.mark.django_db
class TestCategoryAPI:
    """Tests for the Category API endpoints."""

    def test_list_categories_authenticated(self, owner_client, owner, category_factory):
        """Test listing categories as authenticated user."""
        category_factory(restaurant=owner.restaurant, name="Category 1")
        category_factory(restaurant=owner.restaurant, name="Category 2")

        response = owner_client.get("/api/v1/menu/categories/")
        assert response.status_code == 200
        assert response.data["count"] == 2

    def test_list_categories_unauthenticated(self, api_client):
        """Test listing categories requires authentication."""
        response = api_client.get("/api/v1/menu/categories/")
        assert response.status_code == 401

    def test_create_category_as_owner(self, owner_client, owner):
        """Test owner can create category."""
        data = {
            "name": "New Category",
            "display_order": 1,
            "is_visible": True,
        }
        response = owner_client.post("/api/v1/menu/categories/", data)
        assert response.status_code == 201
        assert response.data["name"] == "New Category"

        # Verify category was created with correct restaurant
        category = Category.all_objects.get(id=response.data["id"])
        assert category.restaurant == owner.restaurant

    def test_create_category_as_manager(self, manager_client, manager):
        """Test manager can create category."""
        data = {"name": "Manager Category", "display_order": 1}
        response = manager_client.post("/api/v1/menu/categories/", data)
        assert response.status_code == 201

    def test_create_category_as_cashier_forbidden(self, cashier_client, cashier):
        """Test cashier cannot create category."""
        data = {"name": "Cashier Category", "display_order": 1}
        response = cashier_client.post("/api/v1/menu/categories/", data)
        assert response.status_code == 403

    def test_update_category(self, owner_client, owner, category_factory):
        """Test owner can update category."""
        category = category_factory(restaurant=owner.restaurant, name="Old Name")

        data = {"name": "New Name", "display_order": 2}
        response = owner_client.patch(
            f"/api/v1/menu/categories/{category.id}/", data
        )
        assert response.status_code == 200
        assert response.data["name"] == "New Name"

    def test_delete_category(self, owner_client, owner, category_factory):
        """Test owner can delete category."""
        category = category_factory(restaurant=owner.restaurant)

        response = owner_client.delete(f"/api/v1/menu/categories/{category.id}/")
        assert response.status_code == 204
        assert not Category.all_objects.filter(id=category.id).exists()

    def test_invisible_category_hidden_from_cashier(
        self, cashier_client, cashier, category_factory
    ):
        """Test invisible categories are hidden from non-managers."""
        category_factory(restaurant=cashier.restaurant, name="Visible", is_visible=True)
        category_factory(
            restaurant=cashier.restaurant, name="Hidden", is_visible=False
        )

        response = cashier_client.get("/api/v1/menu/categories/")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Visible"

    def test_invisible_category_visible_to_owner(
        self, owner_client, owner, category_factory
    ):
        """Test owners can see invisible categories."""
        category_factory(restaurant=owner.restaurant, name="Visible", is_visible=True)
        category_factory(restaurant=owner.restaurant, name="Hidden", is_visible=False)

        response = owner_client.get("/api/v1/menu/categories/")
        assert response.status_code == 200
        assert response.data["count"] == 2


@pytest.mark.django_db
class TestMenuItemAPI:
    """Tests for the MenuItem API endpoints."""

    def test_list_menu_items(
        self, owner_client, owner, menu_item_factory, category_factory
    ):
        """Test listing menu items."""
        category = category_factory(restaurant=owner.restaurant)
        menu_item_factory(category=category, restaurant=owner.restaurant)
        menu_item_factory(category=category, restaurant=owner.restaurant)

        response = owner_client.get("/api/v1/menu/items/")
        assert response.status_code == 200
        assert response.data["count"] == 2

    def test_create_menu_item(self, owner_client, owner, category_factory):
        """Test creating a menu item."""
        category = category_factory(restaurant=owner.restaurant)

        data = {
            "category": str(category.id),
            "name": "Burger",
            "description": "Delicious burger",
            "price": 5000,
            "is_available": True,
        }
        response = owner_client.post("/api/v1/menu/items/", data)
        assert response.status_code == 201
        assert response.data["name"] == "Burger"
        assert response.data["price"] == 5000

    def test_create_menu_item_negative_price_fails(
        self, owner_client, owner, category_factory
    ):
        """Test creating menu item with negative price fails."""
        category = category_factory(restaurant=owner.restaurant)

        data = {
            "category": str(category.id),
            "name": "Burger",
            "price": -100,
        }
        response = owner_client.post("/api/v1/menu/items/", data)
        assert response.status_code == 400

    def test_filter_items_by_category(
        self, owner_client, owner, menu_item_factory, category_factory
    ):
        """Test filtering menu items by category."""
        category1 = category_factory(restaurant=owner.restaurant, name="Cat 1")
        category2 = category_factory(restaurant=owner.restaurant, name="Cat 2")

        menu_item_factory(
            category=category1, restaurant=owner.restaurant, name="Item 1"
        )
        menu_item_factory(
            category=category2, restaurant=owner.restaurant, name="Item 2"
        )

        response = owner_client.get(f"/api/v1/menu/items/?category_id={category1.id}")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Item 1"

    def test_menu_item_includes_modifiers(
        self, owner_client, owner, menu_item_factory, modifier_factory, category_factory
    ):
        """Test menu item serialization includes modifiers."""
        category = category_factory(restaurant=owner.restaurant)
        item = menu_item_factory(category=category, restaurant=owner.restaurant)
        modifier_factory(menu_item=item, restaurant=owner.restaurant, name="Size")

        response = owner_client.get(f"/api/v1/menu/items/{item.id}/")
        assert response.status_code == 200
        assert len(response.data["modifiers"]) == 1
        assert response.data["modifiers"][0]["name"] == "Size"


@pytest.mark.django_db
class TestModifierAPI:
    """Tests for the Modifier API endpoints."""

    def test_list_modifiers(
        self, owner_client, owner, modifier_factory, menu_item_factory, category_factory
    ):
        """Test listing modifiers."""
        category = category_factory(restaurant=owner.restaurant)
        item = menu_item_factory(category=category, restaurant=owner.restaurant)
        modifier_factory(menu_item=item, restaurant=owner.restaurant)

        response = owner_client.get("/api/v1/menu/modifiers/")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_create_modifier(
        self, owner_client, owner, menu_item_factory, category_factory
    ):
        """Test creating a modifier."""
        category = category_factory(restaurant=owner.restaurant)
        item = menu_item_factory(category=category, restaurant=owner.restaurant)

        data = {
            "menu_item": str(item.id),
            "name": "Size",
            "required": True,
            "max_selections": 1,
        }
        response = owner_client.post("/api/v1/menu/modifiers/", data)
        assert response.status_code == 201
        assert response.data["name"] == "Size"

    def test_filter_modifiers_by_menu_item(
        self, owner_client, owner, modifier_factory, menu_item_factory, category_factory
    ):
        """Test filtering modifiers by menu item."""
        category = category_factory(restaurant=owner.restaurant)
        item1 = menu_item_factory(category=category, restaurant=owner.restaurant)
        item2 = menu_item_factory(category=category, restaurant=owner.restaurant)

        modifier_factory(menu_item=item1, restaurant=owner.restaurant, name="Mod 1")
        modifier_factory(menu_item=item2, restaurant=owner.restaurant, name="Mod 2")

        response = owner_client.get(f"/api/v1/menu/modifiers/?menu_item_id={item1.id}")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Mod 1"


@pytest.mark.django_db
class TestModifierOptionAPI:
    """Tests for the ModifierOption API endpoints."""

    def test_list_modifier_options(
        self,
        owner_client,
        owner,
        modifier_option_factory,
        modifier_factory,
        menu_item_factory,
        category_factory,
    ):
        """Test listing modifier options."""
        category = category_factory(restaurant=owner.restaurant)
        item = menu_item_factory(category=category, restaurant=owner.restaurant)
        modifier = modifier_factory(menu_item=item, restaurant=owner.restaurant)
        modifier_option_factory(modifier=modifier, restaurant=owner.restaurant)

        response = owner_client.get("/api/v1/menu/modifier-options/")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_create_modifier_option(
        self,
        owner_client,
        owner,
        modifier_factory,
        menu_item_factory,
        category_factory,
    ):
        """Test creating a modifier option."""
        category = category_factory(restaurant=owner.restaurant)
        item = menu_item_factory(category=category, restaurant=owner.restaurant)
        modifier = modifier_factory(menu_item=item, restaurant=owner.restaurant)

        data = {
            "modifier": str(modifier.id),
            "name": "Large",
            "price_adjustment": 500,
            "is_available": True,
        }
        response = owner_client.post("/api/v1/menu/modifier-options/", data)
        assert response.status_code == 201
        assert response.data["name"] == "Large"
        assert response.data["price_adjustment"] == 500


@pytest.mark.django_db
class TestFullMenuAPI:
    """Tests for the full menu API endpoint."""

    def test_full_menu_returns_nested_structure(self, owner_client, owner, sample_menu):
        """Test full menu returns nested categories/items/modifiers."""
        response = owner_client.get("/api/v1/menu/full/")
        assert response.status_code == 200
        assert "categories" in response.data

        # Should have 3 categories (owner sees all including hidden)
        categories = response.data["categories"]
        assert len(categories) == 3

        # Check nested items
        entrees = next(c for c in categories if c["name"] == "Entrees")
        assert len(entrees["items"]) >= 1

        # Check nested modifiers
        burger = next((i for i in entrees["items"] if i["name"] == "Burger"), None)
        if burger:
            assert len(burger["modifiers"]) == 2

    def test_full_menu_hides_invisible_for_cashier(
        self, cashier_client, cashier, sample_menu
    ):
        """Test cashier only sees visible categories and available items."""
        # Set the cashier's restaurant to the sample menu restaurant
        cashier.restaurant = sample_menu["restaurant"]
        cashier.save()

        response = cashier_client.get("/api/v1/menu/full/")
        assert response.status_code == 200

        categories = response.data["categories"]
        # Should only see 2 visible categories (Entrees, Drinks)
        # Desserts is invisible
        category_names = [c["name"] for c in categories]
        assert "Desserts" not in category_names
        assert len(categories) == 2

    def test_full_menu_requires_authentication(self, api_client):
        """Test full menu requires authentication."""
        response = api_client.get("/api/v1/menu/full/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestMultiTenantIsolation:
    """Tests for multi-tenant data isolation."""

    def test_user_cannot_see_other_restaurant_categories(
        self, owner_client, owner, category_factory, restaurant_factory
    ):
        """Test user cannot access another restaurant's categories."""
        # Create category for another restaurant
        other_restaurant = restaurant_factory()
        category_factory(restaurant=other_restaurant, name="Other Category")

        # Create category for owner's restaurant
        category_factory(restaurant=owner.restaurant, name="Own Category")

        # Owner should only see their own categories
        response = owner_client.get("/api/v1/menu/categories/")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Own Category"

    def test_user_cannot_see_other_restaurant_items(
        self,
        owner_client,
        owner,
        menu_item_factory,
        category_factory,
        restaurant_factory,
    ):
        """Test user cannot access another restaurant's menu items."""
        # Create items for another restaurant
        other_restaurant = restaurant_factory()
        other_category = category_factory(restaurant=other_restaurant)
        menu_item_factory(
            restaurant=other_restaurant, category=other_category, name="Other Item"
        )

        # Create items for owner's restaurant
        own_category = category_factory(restaurant=owner.restaurant)
        menu_item_factory(
            restaurant=owner.restaurant, category=own_category, name="Own Item"
        )

        # Owner should only see their own items
        response = owner_client.get("/api/v1/menu/items/")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Own Item"

    def test_full_menu_only_shows_own_restaurant(
        self, owner_client, owner, sample_menu, category_factory, restaurant_factory
    ):
        """Test full menu only shows own restaurant's data."""
        # Create data for another restaurant
        other_restaurant = restaurant_factory()
        category_factory(restaurant=other_restaurant, name="Other Restaurant Category")

        response = owner_client.get("/api/v1/menu/full/")
        assert response.status_code == 200

        # All categories should belong to owner's restaurant
        category_names = [c["name"] for c in response.data["categories"]]
        assert "Other Restaurant Category" not in category_names
