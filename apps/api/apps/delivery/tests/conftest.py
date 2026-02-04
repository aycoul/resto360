"""Pytest configuration for delivery tests."""

import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.tests.factories import RestaurantFactory, UserFactory
from apps.orders.tests.factories import OrderFactory

from .factories import DeliveryFactory, DeliveryZoneFactory, DriverFactory

# Register factories as pytest fixtures
register(RestaurantFactory)
register(UserFactory)
register(DeliveryZoneFactory)
register(DriverFactory, "driver_profile")  # Avoid conflict with auth DriverFactory
register(OrderFactory)
register(DeliveryFactory)


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    """Authenticated API client for regular user."""
    # Ensure user has restaurant attribute set on request
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def order(restaurant):
    """Create an order for testing delivery."""
    return OrderFactory(restaurant=restaurant, order_type="delivery")


@pytest.fixture
def polygon_abidjan():
    """Sample polygon covering central Abidjan (Plateau district)."""
    # Approximate coordinates for Plateau, Abidjan
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [-4.0200, 5.3200],  # SW corner
                [-4.0200, 5.3400],  # NW corner
                [-4.0000, 5.3400],  # NE corner
                [-4.0000, 5.3200],  # SE corner
                [-4.0200, 5.3200],  # Close polygon
            ]
        ],
    }


@pytest.fixture
def point_inside_abidjan():
    """Point inside the Abidjan polygon."""
    return {"lat": 5.3300, "lng": -4.0100}


@pytest.fixture
def point_outside_abidjan():
    """Point outside the Abidjan polygon."""
    return {"lat": 5.4000, "lng": -3.9000}
