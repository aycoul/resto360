"""Tests for WebSocket consumers."""

import pytest
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken

from apps.orders.middleware import JWTAuthMiddleware
from apps.orders.routing import websocket_urlpatterns

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def application():
    """Create the ASGI application for testing."""
    return JWTAuthMiddleware(URLRouter(websocket_urlpatterns))


@pytest.fixture
def other_restaurant(restaurant_factory):
    """Create a different restaurant for multi-tenant testing."""
    return restaurant_factory(name="Other Restaurant")


@pytest.mark.asyncio
async def test_kitchen_consumer_connect_authenticated(application, owner):
    """Test authenticated user can connect to kitchen WebSocket."""
    token = AccessToken.for_user(owner)
    communicator = WebsocketCommunicator(
        application, f"/ws/kitchen/{owner.restaurant_id}/?token={token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    # Should receive initial queue
    response = await communicator.receive_json_from()
    assert response["type"] == "initial_queue"
    assert "orders" in response
    assert isinstance(response["orders"], list)

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_kitchen_consumer_connect_as_cashier(application, cashier):
    """Test cashier can connect to their restaurant's kitchen WebSocket."""
    token = AccessToken.for_user(cashier)
    communicator = WebsocketCommunicator(
        application, f"/ws/kitchen/{cashier.restaurant_id}/?token={token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    # Should receive initial queue
    response = await communicator.receive_json_from()
    assert response["type"] == "initial_queue"

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_kitchen_consumer_connect_as_kitchen_staff(application, kitchen_user):
    """Test kitchen staff can connect to their restaurant's kitchen WebSocket."""
    token = AccessToken.for_user(kitchen_user)
    communicator = WebsocketCommunicator(
        application, f"/ws/kitchen/{kitchen_user.restaurant_id}/?token={token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    response = await communicator.receive_json_from()
    assert response["type"] == "initial_queue"

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_kitchen_consumer_reject_unauthenticated(application):
    """Test unauthenticated user cannot connect to kitchen WebSocket."""
    communicator = WebsocketCommunicator(
        application, "/ws/kitchen/00000000-0000-0000-0000-000000000000/"
    )

    connected, subprotocol = await communicator.connect()
    # Connection should be closed with code 4001 (unauthenticated)
    assert not connected


@pytest.mark.asyncio
async def test_kitchen_consumer_reject_invalid_token(application):
    """Test invalid JWT token is rejected."""
    communicator = WebsocketCommunicator(
        application,
        "/ws/kitchen/00000000-0000-0000-0000-000000000000/?token=invalid-token",
    )

    connected, _ = await communicator.connect()
    assert not connected


@pytest.mark.asyncio
async def test_kitchen_consumer_reject_wrong_restaurant(
    application, owner, other_restaurant
):
    """Test user cannot connect to different restaurant's kitchen."""
    token = AccessToken.for_user(owner)
    # Try to connect to a different restaurant's kitchen
    communicator = WebsocketCommunicator(
        application, f"/ws/kitchen/{other_restaurant.id}/?token={token}"
    )

    connected, _ = await communicator.connect()
    # Connection should be closed with code 4003 (wrong restaurant)
    assert not connected


@pytest.mark.asyncio
async def test_kitchen_consumer_receives_order_created(application, owner):
    """Test kitchen display receives new order notification."""
    from channels.layers import get_channel_layer

    token = AccessToken.for_user(owner)
    communicator = WebsocketCommunicator(
        application, f"/ws/kitchen/{owner.restaurant_id}/?token={token}"
    )

    await communicator.connect()

    # Clear initial queue message
    await communicator.receive_json_from()

    # Simulate order creation notification via channel layer
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"kitchen_{owner.restaurant_id}",
        {
            "type": "order_created",
            "order": {"id": "test-order-id", "order_number": 42, "status": "pending"},
        },
    )

    response = await communicator.receive_json_from()
    assert response["type"] == "order_created"
    assert response["order"]["id"] == "test-order-id"
    assert response["order"]["order_number"] == 42

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_kitchen_consumer_receives_order_updated(application, owner):
    """Test kitchen display receives order update notification."""
    from channels.layers import get_channel_layer

    token = AccessToken.for_user(owner)
    communicator = WebsocketCommunicator(
        application, f"/ws/kitchen/{owner.restaurant_id}/?token={token}"
    )

    await communicator.connect()
    await communicator.receive_json_from()  # Clear initial queue

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"kitchen_{owner.restaurant_id}",
        {
            "type": "order_updated",
            "order": {"id": "test-order-id", "order_number": 42, "notes": "Updated"},
        },
    )

    response = await communicator.receive_json_from()
    assert response["type"] == "order_updated"
    assert response["order"]["notes"] == "Updated"

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_kitchen_consumer_receives_status_changed(application, owner):
    """Test kitchen display receives status change notification."""
    from channels.layers import get_channel_layer

    token = AccessToken.for_user(owner)
    communicator = WebsocketCommunicator(
        application, f"/ws/kitchen/{owner.restaurant_id}/?token={token}"
    )

    await communicator.connect()
    await communicator.receive_json_from()  # Clear initial queue

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"kitchen_{owner.restaurant_id}",
        {
            "type": "order_status_changed",
            "order_id": "test-order-id",
            "status": "preparing",
            "previous_status": "pending",
        },
    )

    response = await communicator.receive_json_from()
    assert response["type"] == "order_status_changed"
    assert response["order_id"] == "test-order-id"
    assert response["status"] == "preparing"
    assert response["previous_status"] == "pending"

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_kitchen_consumer_multiple_clients(application, owner, cashier):
    """Test multiple clients in same restaurant receive same notifications."""
    from channels.layers import get_channel_layer

    # Connect owner
    owner_token = AccessToken.for_user(owner)
    owner_comm = WebsocketCommunicator(
        application, f"/ws/kitchen/{owner.restaurant_id}/?token={owner_token}"
    )
    await owner_comm.connect()
    await owner_comm.receive_json_from()  # Clear initial queue

    # Connect cashier (same restaurant)
    cashier_token = AccessToken.for_user(cashier)
    cashier_comm = WebsocketCommunicator(
        application, f"/ws/kitchen/{cashier.restaurant_id}/?token={cashier_token}"
    )
    await cashier_comm.connect()
    await cashier_comm.receive_json_from()  # Clear initial queue

    # Send notification
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"kitchen_{owner.restaurant_id}",
        {"type": "order_created", "order": {"id": "shared-order", "order_number": 1}},
    )

    # Both clients should receive the notification
    owner_response = await owner_comm.receive_json_from()
    cashier_response = await cashier_comm.receive_json_from()

    assert owner_response["type"] == "order_created"
    assert cashier_response["type"] == "order_created"
    assert owner_response["order"]["id"] == "shared-order"
    assert cashier_response["order"]["id"] == "shared-order"

    await owner_comm.disconnect()
    await cashier_comm.disconnect()


@pytest.mark.asyncio
async def test_kitchen_consumer_handles_malformed_json(application, owner):
    """Test consumer handles malformed JSON input gracefully."""
    token = AccessToken.for_user(owner)
    communicator = WebsocketCommunicator(
        application, f"/ws/kitchen/{owner.restaurant_id}/?token={token}"
    )

    await communicator.connect()
    await communicator.receive_json_from()  # Clear initial queue

    # Send malformed JSON - should not crash
    await communicator.send_to(text_data="not-valid-json{")

    # Connection should still be alive - send a valid message to verify
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"kitchen_{owner.restaurant_id}",
        {"type": "order_created", "order": {"id": "test", "order_number": 1}},
    )

    response = await communicator.receive_json_from()
    assert response["type"] == "order_created"

    await communicator.disconnect()
