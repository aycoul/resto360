import pytest

from apps.authentication.models import User

pytestmark = pytest.mark.django_db


class TestRestaurantModel:
    """Tests for Restaurant model."""

    def test_create_restaurant(self, restaurant_factory):
        restaurant = restaurant_factory(name="Chez Mama", slug="chez-mama")
        assert restaurant.name == "Chez Mama"
        assert restaurant.slug == "chez-mama"
        assert restaurant.currency == "XOF"
        assert restaurant.timezone == "Africa/Abidjan"

    def test_restaurant_str(self, restaurant_factory):
        restaurant = restaurant_factory(name="Test Restaurant")
        assert str(restaurant) == "Test Restaurant"

    def test_restaurant_has_uuid_id(self, restaurant_factory):
        restaurant = restaurant_factory()
        assert restaurant.id is not None
        assert len(str(restaurant.id)) == 36  # UUID format

    def test_restaurant_default_active(self, restaurant_factory):
        restaurant = restaurant_factory()
        assert restaurant.is_active is True


class TestUserModel:
    """Tests for User model."""

    def test_create_user(self, user_factory, restaurant_factory):
        restaurant = restaurant_factory()
        user = user_factory(
            phone="+2250701234567",
            name="Jean Dupont",
            restaurant=restaurant,
            role="cashier",
        )
        assert user.phone == "+2250701234567"
        assert user.name == "Jean Dupont"
        assert user.role == "cashier"
        assert user.restaurant == restaurant

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            phone="+2250700000000",
            password="adminpass123",
            name="Admin User",
        )
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.role == "owner"

    def test_user_str(self, user_factory):
        user = user_factory(name="Jean Dupont", phone="+2250701234567")
        assert str(user) == "Jean Dupont (+2250701234567)"

    def test_owner_permissions(self, owner_factory):
        owner = owner_factory()
        permissions = owner.get_permissions_list()
        assert "manage_restaurant" in permissions
        assert "manage_staff" in permissions
        assert "manage_menu" in permissions
        assert "view_reports" in permissions
        assert "view_menu" in permissions  # base permission
        assert "view_orders" in permissions  # base permission

    def test_manager_permissions(self, manager_factory):
        manager = manager_factory()
        permissions = manager.get_permissions_list()
        assert "manage_menu" in permissions
        assert "view_reports" in permissions
        assert "manage_orders" in permissions
        assert "manage_restaurant" not in permissions
        assert "manage_staff" not in permissions

    def test_cashier_permissions(self, cashier_factory):
        cashier = cashier_factory()
        permissions = cashier.get_permissions_list()
        assert "create_orders" in permissions
        assert "manage_orders" in permissions
        assert "manage_restaurant" not in permissions
        assert "manage_menu" not in permissions

    def test_password_hashing(self, user_factory):
        user = user_factory(password="mypassword123")
        assert user.check_password("mypassword123")
        assert not user.check_password("wrongpassword")

    def test_user_has_uuid_id(self, user_factory):
        user = user_factory()
        assert user.id is not None
        assert len(str(user.id)) == 36  # UUID format

    def test_user_default_language_french(self, user_factory):
        user = user_factory()
        assert user.language == "fr"

    def test_user_without_password_fails(self):
        with pytest.raises(ValueError, match="phone number"):
            User.objects.create_user(phone=None, password="test123")
