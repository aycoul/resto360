import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestOwnerRegistration:
    """Tests for owner registration endpoint."""

    def test_register_owner_success(self, api_client):
        url = reverse("authentication:register_owner")
        data = {
            "phone": "+2250712345678",
            "name": "Jean Owner",
            "email": "jean@example.com",
            "password": "securepass123",
            "business_name": "Chez Jean",
            "business_slug": "chez-jean",
            "business_phone": "+2250712345678",
            "business_address": "123 Rue d'Abidjan",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "user" in response.data
        assert "tokens" in response.data
        assert response.data["user"]["role"] == "owner"
        assert response.data["user"]["restaurant"]["name"] == "Chez Jean"

    def test_register_returns_valid_tokens(self, api_client):
        url = reverse("authentication:register_owner")
        data = {
            "phone": "+2250712345679",
            "name": "Token Test Owner",
            "password": "securepass123",
            "business_name": "Token Restaurant",
            "business_slug": "token-restaurant",
        }
        response = api_client.post(url, data, format="json")

        assert "tokens" in response.data
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]
        # Tokens should be non-empty strings
        assert len(response.data["tokens"]["access"]) > 0
        assert len(response.data["tokens"]["refresh"]) > 0

    def test_register_duplicate_phone_fails(self, api_client, user_factory):
        user_factory(phone="+2250712345678")
        url = reverse("authentication:register_owner")
        data = {
            "phone": "+2250712345678",  # Duplicate
            "name": "Another Owner",
            "password": "securepass123",
            "business_name": "Another Restaurant",
            "business_slug": "another-restaurant",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in response.data

    def test_register_duplicate_slug_fails(self, api_client, business_factory):
        business_factory(slug="existing-slug")
        url = reverse("authentication:register_owner")
        data = {
            "phone": "+2250712345680",
            "name": "New Owner",
            "password": "securepass123",
            "business_name": "New Restaurant",
            "business_slug": "existing-slug",  # Duplicate
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "business_slug" in response.data


class TestLogin:
    """Tests for login endpoint."""

    def test_login_success(self, api_client, user_factory):
        user_factory(phone="+2250712345678", password="testpass123")
        url = reverse("authentication:token_obtain_pair")
        data = {"phone": "+2250712345678", "password": "testpass123"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_invalid_password(self, api_client, user_factory):
        user_factory(phone="+2250712345678", password="testpass123")
        url = reverse("authentication:token_obtain_pair")
        data = {"phone": "+2250712345678", "password": "wrongpassword"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client):
        url = reverse("authentication:token_obtain_pair")
        data = {"phone": "+2250799999999", "password": "anypassword"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_jwt_contains_custom_claims(self, api_client, owner_factory):
        import jwt

        owner = owner_factory(phone="+2250712345678", password="testpass123")
        url = reverse("authentication:token_obtain_pair")
        data = {"phone": "+2250712345678", "password": "testpass123"}

        response = api_client.post(url, data, format="json")

        # Decode token (without verification for testing)
        token = response.data["access"]
        decoded = jwt.decode(token, options={"verify_signature": False})

        assert decoded["role"] == "owner"
        assert decoded["name"] == owner.name
        assert "restaurant_id" in decoded
        assert "permissions" in decoded
        assert "manage_business" in decoded["permissions"]


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_token_success(self, api_client, user_factory):
        user_factory(phone="+2250712345678", password="testpass123")

        # Get initial tokens
        login_url = reverse("authentication:token_obtain_pair")
        login_response = api_client.post(
            login_url,
            {"phone": "+2250712345678", "password": "testpass123"},
            format="json",
        )
        refresh_token = login_response.data["refresh"]

        # Refresh the token
        refresh_url = reverse("authentication:token_refresh")
        response = api_client.post(
            refresh_url, {"refresh": refresh_token}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_invalid_token_fails(self, api_client):
        refresh_url = reverse("authentication:token_refresh")
        response = api_client.post(
            refresh_url, {"refresh": "invalid-token"}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_blacklists_token(self, auth_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        url = reverse("authentication:logout")

        response = auth_client.post(url, {"refresh": str(refresh)}, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Try to use the blacklisted refresh token
        refresh_url = reverse("authentication:token_refresh")
        response = auth_client.post(
            refresh_url, {"refresh": str(refresh)}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_without_token_still_succeeds(self, auth_client):
        url = reverse("authentication:logout")
        response = auth_client.post(url, {}, format="json")

        # Logout without providing refresh token should still work
        assert response.status_code == status.HTTP_200_OK


class TestCurrentUser:
    """Tests for current user endpoint."""

    def test_get_current_user(self, auth_client, user):
        url = reverse("authentication:current_user")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["phone"] == user.phone
        assert response.data["name"] == user.name

    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("authentication:current_user")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_current_user_includes_restaurant(self, owner_client, owner):
        url = reverse("authentication:current_user")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "restaurant" in response.data
        assert response.data["restaurant"]["id"] == str(owner.business.id)


class TestStaffInvite:
    """Tests for staff invite endpoint."""

    def test_owner_can_invite_staff(self, owner_client, owner):
        url = reverse("authentication:invite_staff")
        data = {
            "phone": "+2250799999999",
            "name": "New Cashier",
            "password": "staffpass123",
            "role": "cashier",
        }
        response = owner_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["role"] == "cashier"
        assert response.data["restaurant"]["id"] == str(owner.business.id)

    def test_manager_can_invite_staff(self, manager_client, manager):
        url = reverse("authentication:invite_staff")
        data = {
            "phone": "+2250799999998",
            "name": "New Kitchen Staff",
            "password": "staffpass123",
            "role": "kitchen",
        }
        response = manager_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_cashier_cannot_invite_staff(self, api_client, cashier_factory):
        from rest_framework_simplejwt.tokens import RefreshToken

        cashier = cashier_factory()
        refresh = RefreshToken.for_user(cashier)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        url = reverse("authentication:invite_staff")
        data = {
            "phone": "+2250799999997",
            "name": "Unauthorized Invite",
            "password": "staffpass123",
            "role": "driver",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_invite_with_duplicate_phone(self, owner_client, user_factory):
        existing_user = user_factory(phone="+2250799999996")
        url = reverse("authentication:invite_staff")
        data = {
            "phone": existing_user.phone,  # Duplicate
            "name": "Duplicate Phone",
            "password": "staffpass123",
            "role": "cashier",
        }
        response = owner_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in response.data


class TestBusinessSettings:
    """Tests for business settings endpoint."""

    def test_owner_can_get_business(self, owner_client, owner):
        url = reverse("authentication:restaurant_settings")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(owner.business.id)

    def test_owner_can_update_business(self, owner_client, owner):
        url = reverse("authentication:restaurant_settings")
        data = {"name": "Updated Restaurant Name", "address": "New Address"}

        response = owner_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Restaurant Name"

    def test_manager_cannot_update_business(self, manager_client):
        url = reverse("authentication:restaurant_settings")
        data = {"name": "Should Fail"}

        response = manager_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cashier_cannot_access_business_settings(
        self, api_client, cashier_factory
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        cashier = cashier_factory()
        refresh = RefreshToken.for_user(cashier)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        url = reverse("authentication:restaurant_settings")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestMultiTenantIsolation:
    """Tests for multi-tenant isolation."""

    def test_staff_list_only_shows_same_business(
        self, owner_client, owner, user_factory, business_factory
    ):
        # Create staff for owner's business
        staff1 = user_factory(business=owner.business, name="Staff 1")
        staff2 = user_factory(business=owner.business, name="Staff 2")

        # Create staff for different business
        other_business = business_factory()
        other_staff = user_factory(business=other_business, name="Other Staff")

        url = reverse("authentication:staff_list")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Response is paginated
        results = response.data.get("results", response.data)
        phones = [u["phone"] for u in results]

        assert staff1.phone in phones
        assert staff2.phone in phones
        assert owner.phone in phones  # Owner is also staff
        assert other_staff.phone not in phones

    def test_invited_staff_belongs_to_correct_business(
        self, owner_client, owner, business_factory
    ):
        # Create another business
        other_business = business_factory()

        url = reverse("authentication:invite_staff")
        data = {
            "phone": "+2250788888888",
            "name": "New Staff",
            "password": "staffpass123",
            "role": "cashier",
        }
        response = owner_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        # Staff should belong to owner's business, not the other one
        assert response.data["restaurant"]["id"] == str(owner.business.id)
        assert response.data["restaurant"]["id"] != str(other_business.id)


class TestStaffList:
    """Tests for staff list endpoint."""

    def test_owner_can_list_staff(self, owner_client, owner, user_factory):
        # Create additional staff
        user_factory(business=owner.business, role="cashier")
        user_factory(business=owner.business, role="kitchen")

        url = reverse("authentication:staff_list")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Response is paginated - check count or results
        results = response.data.get("results", response.data)
        assert len(results) == 3  # owner + 2 staff

    def test_manager_can_list_staff(self, manager_client, manager, user_factory):
        user_factory(business=manager.business, role="cashier")

        url = reverse("authentication:staff_list")
        response = manager_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_cashier_cannot_list_staff(self, api_client, cashier_factory):
        from rest_framework_simplejwt.tokens import RefreshToken

        cashier = cashier_factory()
        refresh = RefreshToken.for_user(cashier)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        url = reverse("authentication:staff_list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
