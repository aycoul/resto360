import pytest

from apps.authentication.models import User

pytestmark = pytest.mark.django_db


class TestBusinessModel:
    """Tests for Business model."""

    def test_create_business(self, business_factory):
        business = business_factory(name="Chez Mama", slug="chez-mama")
        assert business.name == "Chez Mama"
        assert business.slug == "chez-mama"
        assert business.currency == "XOF"
        assert business.timezone == "Africa/Abidjan"

    def test_business_str(self, business_factory):
        business = business_factory(name="Test Business")
        assert str(business) == "Test Business"

    def test_business_has_uuid_id(self, business_factory):
        business = business_factory()
        assert business.id is not None
        assert len(str(business.id)) == 36  # UUID format

    def test_business_default_active(self, business_factory):
        business = business_factory()
        assert business.is_active is True


class TestUserModel:
    """Tests for User model."""

    def test_create_user(self, user_factory, business_factory):
        business = business_factory()
        user = user_factory(
            phone="+2250701234567",
            name="Jean Dupont",
            business=business,
            role="cashier",
        )
        assert user.phone == "+2250701234567"
        assert user.name == "Jean Dupont"
        assert user.role == "cashier"
        assert user.business == business

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
        assert "manage_business" in permissions
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
        assert "manage_business" not in permissions
        assert "manage_staff" not in permissions

    def test_cashier_permissions(self, cashier_factory):
        cashier = cashier_factory()
        permissions = cashier.get_permissions_list()
        assert "create_orders" in permissions
        assert "manage_orders" in permissions
        assert "manage_business" not in permissions
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
