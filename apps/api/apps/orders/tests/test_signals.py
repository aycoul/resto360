"""Tests for WebSocket signal functions."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apps.orders.signals import (
    notify_kitchen_order_created,
    notify_kitchen_order_updated,
    notify_kitchen_status_changed,
)

pytestmark = pytest.mark.django_db


class TestNotifyKitchenOrderCreated:
    """Tests for notify_kitchen_order_created signal function."""

    def test_sends_to_channel_layer(self, order):
        """Test order created notification sends to channel layer."""
        with patch("apps.orders.signals.get_channel_layer") as mock_get_layer:
            mock_layer = MagicMock()
            mock_layer.group_send = AsyncMock()
            mock_get_layer.return_value = mock_layer

            notify_kitchen_order_created(order)

            mock_layer.group_send.assert_called_once()
            call_args = mock_layer.group_send.call_args
            # Check group name
            assert f"kitchen_{order.business_id}" == call_args[0][0]
            # Check message type
            assert call_args[0][1]["type"] == "order_created"
            # Check order data is included
            assert "order" in call_args[0][1]

    def test_includes_order_data(self, order):
        """Test notification includes serialized order data."""
        with patch("apps.orders.signals.get_channel_layer") as mock_get_layer:
            mock_layer = MagicMock()
            mock_layer.group_send = AsyncMock()
            mock_get_layer.return_value = mock_layer

            notify_kitchen_order_created(order)

            call_args = mock_layer.group_send.call_args
            order_data = call_args[0][1]["order"]
            assert order_data["id"] == str(order.id)
            assert order_data["order_number"] == order.order_number

    def test_handles_missing_channel_layer_gracefully(self, order):
        """Test function handles missing channel layer without error."""
        with patch("apps.orders.signals.get_channel_layer", return_value=None):
            # Should not raise exception
            notify_kitchen_order_created(order)


class TestNotifyKitchenOrderUpdated:
    """Tests for notify_kitchen_order_updated signal function."""

    def test_sends_to_channel_layer(self, order):
        """Test order updated notification sends to channel layer."""
        with patch("apps.orders.signals.get_channel_layer") as mock_get_layer:
            mock_layer = MagicMock()
            mock_layer.group_send = AsyncMock()
            mock_get_layer.return_value = mock_layer

            notify_kitchen_order_updated(order)

            mock_layer.group_send.assert_called_once()
            call_args = mock_layer.group_send.call_args
            assert f"kitchen_{order.business_id}" == call_args[0][0]
            assert call_args[0][1]["type"] == "order_updated"
            assert "order" in call_args[0][1]

    def test_handles_missing_channel_layer_gracefully(self, order):
        """Test function handles missing channel layer without error."""
        with patch("apps.orders.signals.get_channel_layer", return_value=None):
            notify_kitchen_order_updated(order)


class TestNotifyKitchenStatusChanged:
    """Tests for notify_kitchen_status_changed signal function."""

    def test_sends_to_channel_layer(self, order):
        """Test status change notification sends to channel layer."""
        with patch("apps.orders.signals.get_channel_layer") as mock_get_layer:
            mock_layer = MagicMock()
            mock_layer.group_send = AsyncMock()
            mock_get_layer.return_value = mock_layer

            notify_kitchen_status_changed(order)

            mock_layer.group_send.assert_called_once()
            call_args = mock_layer.group_send.call_args
            assert f"kitchen_{order.business_id}" == call_args[0][0]
            assert call_args[0][1]["type"] == "order_status_changed"
            assert call_args[0][1]["order_id"] == str(order.id)
            assert call_args[0][1]["status"] == order.status

    def test_includes_previous_status(self, order):
        """Test notification includes previous status when provided."""
        with patch("apps.orders.signals.get_channel_layer") as mock_get_layer:
            mock_layer = MagicMock()
            mock_layer.group_send = AsyncMock()
            mock_get_layer.return_value = mock_layer

            notify_kitchen_status_changed(order, previous_status="pending")

            call_args = mock_layer.group_send.call_args
            assert call_args[0][1]["previous_status"] == "pending"

    def test_handles_missing_previous_status(self, order):
        """Test notification works without previous status."""
        with patch("apps.orders.signals.get_channel_layer") as mock_get_layer:
            mock_layer = MagicMock()
            mock_layer.group_send = AsyncMock()
            mock_get_layer.return_value = mock_layer

            notify_kitchen_status_changed(order)

            call_args = mock_layer.group_send.call_args
            assert call_args[0][1]["previous_status"] is None

    def test_handles_missing_channel_layer_gracefully(self, order):
        """Test function handles missing channel layer without error."""
        with patch("apps.orders.signals.get_channel_layer", return_value=None):
            notify_kitchen_status_changed(order)


class TestSignalIntegration:
    """Integration tests for signal functions with views."""

    def test_order_creation_triggers_notification(self, owner_client, sample_order_data):
        """Test creating an order via API triggers WebSocket notification."""
        with patch("apps.orders.views.notify_kitchen_order_created") as mock_notify:
            data = {
                "order_type": "dine_in",
                "table_id": str(sample_order_data["table"].id),
                "items": [
                    {
                        "menu_item_id": str(sample_order_data["burger"].id),
                        "quantity": 1,
                    }
                ],
            }

            response = owner_client.post("/api/v1/orders/", data, format="json")
            assert response.status_code == 201

            # Verify notification was called
            mock_notify.assert_called_once()
            # Verify it was called with the created order
            called_order = mock_notify.call_args[0][0]
            assert str(called_order.id) == response.data["id"]

    def test_status_update_triggers_notification(
        self, owner_client, order, sample_order_data
    ):
        """Test updating order status via API triggers WebSocket notification."""
        with patch("apps.orders.views.notify_kitchen_status_changed") as mock_notify:
            response = owner_client.patch(
                f"/api/v1/orders/{order.id}/status/",
                {"status": "preparing"},
                format="json",
            )
            assert response.status_code == 200

            # Verify notification was called
            mock_notify.assert_called_once()
            # Verify it was called with correct arguments
            called_order = mock_notify.call_args[0][0]
            assert str(called_order.id) == str(order.id)
            assert mock_notify.call_args[1]["previous_status"] == "pending"
