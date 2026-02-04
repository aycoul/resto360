"""Tests for WebSocket consumers."""

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser

from apps.delivery.consumers import DeliveryTrackingConsumer, DriverLocationConsumer
from apps.delivery.models import Delivery

from .factories import DeliveryFactory, DriverFactory


@pytest.fixture
def driver_with_location(restaurant, user):
    """Create a driver with location for testing."""
    driver = DriverFactory(restaurant=restaurant, user=user, is_available=True)
    driver.update_location(lat=5.33, lng=-4.01)
    return driver


@pytest.fixture
def delivery_with_driver(restaurant, driver_with_location):
    """Create a delivery with assigned driver."""
    delivery = DeliveryFactory(restaurant=restaurant)
    delivery.assign(driver_with_location)
    delivery.save()
    return delivery


class TestDriverLocationConsumer:
    """Tests for DriverLocationConsumer."""

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_connect_requires_auth(self):
        """Test that connection requires authentication."""
        communicator = WebsocketCommunicator(
            DriverLocationConsumer.as_asgi(),
            "/ws/driver/test-id/location/",
        )
        communicator.scope["url_route"] = {"kwargs": {"driver_id": "test-id"}}
        communicator.scope["user"] = AnonymousUser()

        connected, _ = await communicator.connect()

        # Should not connect for anonymous user
        assert connected is False or await communicator.receive_output() == {"type": "websocket.close", "code": 4001}

        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_connect_wrong_driver(self, user, restaurant):
        """Test that user can only connect to their own driver profile."""
        # Create a different driver
        other_driver = await database_sync_to_async(DriverFactory)(restaurant=restaurant)

        communicator = WebsocketCommunicator(
            DriverLocationConsumer.as_asgi(),
            f"/ws/driver/{other_driver.id}/location/",
        )
        communicator.scope["url_route"] = {"kwargs": {"driver_id": str(other_driver.id)}}
        communicator.scope["user"] = user

        connected, _ = await communicator.connect()

        # Should reject for wrong driver
        assert connected is False or await communicator.receive_output() == {"type": "websocket.close", "code": 4003}

        await communicator.disconnect()


class TestDeliveryTrackingConsumer:
    """Tests for DeliveryTrackingConsumer."""

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_connect_with_valid_delivery(self, delivery_with_driver):
        """Test successful connection with valid delivery."""
        delivery = delivery_with_driver

        communicator = WebsocketCommunicator(
            DeliveryTrackingConsumer.as_asgi(),
            f"/ws/delivery/{delivery.id}/track/",
        )
        communicator.scope["url_route"] = {"kwargs": {"delivery_id": str(delivery.id)}}

        connected, _ = await communicator.connect()

        assert connected is True

        # Should receive initial delivery info
        response = await communicator.receive_json_from()
        assert response["type"] == "delivery_info"
        assert response["delivery"]["id"] == str(delivery.id)

        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_connect_invalid_delivery(self):
        """Test connection fails for non-existent delivery."""
        import uuid

        communicator = WebsocketCommunicator(
            DeliveryTrackingConsumer.as_asgi(),
            f"/ws/delivery/{uuid.uuid4()}/track/",
        )
        communicator.scope["url_route"] = {"kwargs": {"delivery_id": str(uuid.uuid4())}}

        connected, _ = await communicator.connect()

        # Should not connect for invalid delivery
        assert connected is False or await communicator.receive_output() == {"type": "websocket.close", "code": 4004}

        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_delivery_info_contains_driver(self, delivery_with_driver):
        """Test delivery info includes driver details when assigned."""
        delivery = delivery_with_driver

        communicator = WebsocketCommunicator(
            DeliveryTrackingConsumer.as_asgi(),
            f"/ws/delivery/{delivery.id}/track/",
        )
        communicator.scope["url_route"] = {"kwargs": {"delivery_id": str(delivery.id)}}

        await communicator.connect()

        response = await communicator.receive_json_from()
        assert "driver" in response["delivery"]
        assert response["delivery"]["driver"]["vehicle_type"] == "motorcycle"

        await communicator.disconnect()
