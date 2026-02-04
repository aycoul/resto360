"""Tests for delivery zone models and API."""

import pytest
from django.contrib.gis.geos import Polygon
from rest_framework import status

from apps.delivery.models import DeliveryZone

from .factories import DeliveryZoneFactory


@pytest.mark.django_db
class TestDeliveryZoneModel:
    """Tests for DeliveryZone model."""

    def test_create_zone(self, restaurant):
        """Test creating a delivery zone."""
        polygon = Polygon(
            [
                (-4.02, 5.32),
                (-4.02, 5.34),
                (-4.00, 5.34),
                (-4.00, 5.32),
                (-4.02, 5.32),
            ],
            srid=4326,
        )

        zone = DeliveryZone.objects.create(
            restaurant=restaurant,
            name="Central Zone",
            polygon=polygon,
            delivery_fee=1500,
            minimum_order=5000,
        )

        assert zone.id is not None
        assert zone.name == "Central Zone"
        assert zone.delivery_fee == 1500

    def test_contains_point_inside(self, restaurant, point_inside_abidjan):
        """Test point inside zone returns True."""
        zone = DeliveryZoneFactory(restaurant=restaurant)

        result = zone.contains_point(
            lat=point_inside_abidjan["lat"], lng=point_inside_abidjan["lng"]
        )

        assert result is True

    def test_contains_point_outside(self, restaurant, point_outside_abidjan):
        """Test point outside zone returns False."""
        zone = DeliveryZoneFactory(restaurant=restaurant)

        result = zone.contains_point(
            lat=point_outside_abidjan["lat"], lng=point_outside_abidjan["lng"]
        )

        assert result is False

    def test_find_zone_for_location(self, restaurant, point_inside_abidjan):
        """Test finding zone for a location."""
        zone = DeliveryZoneFactory(restaurant=restaurant)

        found = DeliveryZone.find_zone_for_location(
            restaurant=restaurant,
            lat=point_inside_abidjan["lat"],
            lng=point_inside_abidjan["lng"],
        )

        assert found == zone

    def test_find_zone_for_location_outside(self, restaurant, point_outside_abidjan):
        """Test no zone found for location outside all zones."""
        DeliveryZoneFactory(restaurant=restaurant)

        found = DeliveryZone.find_zone_for_location(
            restaurant=restaurant,
            lat=point_outside_abidjan["lat"],
            lng=point_outside_abidjan["lng"],
        )

        assert found is None

    def test_inactive_zone_not_found(self, restaurant, point_inside_abidjan):
        """Test inactive zones are not returned."""
        DeliveryZoneFactory(restaurant=restaurant, is_active=False)

        found = DeliveryZone.find_zone_for_location(
            restaurant=restaurant,
            lat=point_inside_abidjan["lat"],
            lng=point_inside_abidjan["lng"],
        )

        assert found is None


@pytest.mark.django_db
class TestDeliveryZoneAPI:
    """Tests for delivery zone API endpoints."""

    def test_list_zones(self, auth_client, restaurant):
        """Test listing delivery zones."""
        DeliveryZoneFactory(restaurant=restaurant)
        DeliveryZoneFactory(restaurant=restaurant)

        response = auth_client.get("/api/v1/delivery/zones/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_list_zones_tenant_isolation(self, auth_client, restaurant):
        """Test zones are filtered by restaurant."""
        DeliveryZoneFactory(restaurant=restaurant)
        DeliveryZoneFactory()  # Different restaurant

        response = auth_client.get("/api/v1/delivery/zones/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_zone(self, auth_client, restaurant, polygon_abidjan):
        """Test creating a delivery zone via API."""
        data = {
            "name": "New Zone",
            "polygon": polygon_abidjan,
            "delivery_fee": 2000,
            "minimum_order": 10000,
            "estimated_time_minutes": 45,
        }

        response = auth_client.post(
            "/api/v1/delivery/zones/", data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["properties"]["name"] == "New Zone"
        assert response.data["properties"]["delivery_fee"] == 2000

    def test_retrieve_zone_geojson(self, auth_client, restaurant):
        """Test retrieving zone returns GeoJSON."""
        zone = DeliveryZoneFactory(restaurant=restaurant)

        response = auth_client.get(f"/api/v1/delivery/zones/{zone.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["type"] == "Feature"
        assert response.data["geometry"]["type"] == "Polygon"
        assert "coordinates" in response.data["geometry"]

    def test_check_address_deliverable(
        self, auth_client, restaurant, point_inside_abidjan
    ):
        """Test check_address returns zone when deliverable."""
        zone = DeliveryZoneFactory(restaurant=restaurant)

        response = auth_client.post(
            "/api/v1/delivery/zones/check_address/",
            point_inside_abidjan,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["deliverable"] is True
        assert response.data["zone"]["id"] == str(zone.id)
        assert response.data["zone"]["delivery_fee"] == zone.delivery_fee

    def test_check_address_not_deliverable(
        self, auth_client, restaurant, point_outside_abidjan
    ):
        """Test check_address returns not deliverable for outside address."""
        DeliveryZoneFactory(restaurant=restaurant)

        response = auth_client.post(
            "/api/v1/delivery/zones/check_address/",
            point_outside_abidjan,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["deliverable"] is False
        assert response.data["zone"] is None
        assert "outside" in response.data["message"].lower()

    def test_check_address_validation(self, auth_client, restaurant):
        """Test check_address validates coordinates."""
        response = auth_client.post(
            "/api/v1/delivery/zones/check_address/",
            {"lat": "invalid", "lng": -4.0},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
