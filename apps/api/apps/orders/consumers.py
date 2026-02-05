"""WebSocket consumers for kitchen display system."""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class KitchenConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for kitchen display.

    Handles real-time order updates for kitchen staff.
    Connected clients receive:
    - Initial queue of pending/preparing orders on connect
    - New order notifications
    - Order status change notifications

    Authentication: JWT token via query string (?token=xxx)
    Multi-tenant: Users can only connect to their business's kitchen
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.business_id = self.scope["url_route"]["kwargs"]["business_id"]

        # Verify user is authenticated and belongs to this business
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        # Verify user has access to this business
        user_business_id = await self.get_user_business_id(user)
        if str(user_business_id) != self.business_id:
            await self.close(code=4003)
            return

        self.room_group_name = f"kitchen_{self.business_id}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Send current queue on connect
        queue = await self.get_kitchen_queue()
        await self.send(
            text_data=json.dumps({"type": "initial_queue", "orders": queue})
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming messages from kitchen display."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message_type = data.get("type")

        if message_type == "update_status":
            order_id = data.get("order_id")
            new_status = data.get("status")
            if order_id and new_status:
                success = await self.update_order_status(order_id, new_status)
                if not success:
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "error",
                                "message": "Failed to update order status",
                            }
                        )
                    )

    async def order_created(self, event):
        """
        Handle new order event.

        Called by channel layer group_send with type='order_created'.
        """
        await self.send(
            text_data=json.dumps({"type": "order_created", "order": event["order"]})
        )

    async def order_updated(self, event):
        """
        Handle order update event.

        Called by channel layer group_send with type='order_updated'.
        """
        await self.send(
            text_data=json.dumps({"type": "order_updated", "order": event["order"]})
        )

    async def order_status_changed(self, event):
        """
        Handle status change event.

        Called by channel layer group_send with type='order_status_changed'.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "order_status_changed",
                    "order_id": event["order_id"],
                    "status": event["status"],
                    "previous_status": event.get("previous_status"),
                }
            )
        )

    @database_sync_to_async
    def get_user_business_id(self, user):
        """Get user's restaurant ID (sync to async wrapper)."""
        return user.business_id

    @database_sync_to_async
    def get_kitchen_queue(self):
        """Get current kitchen queue (pending/preparing/ready orders)."""
        from apps.orders.models import Order, OrderStatus
        from apps.orders.serializers import OrderSerializer

        orders = (
            Order.all_objects.filter(
                business_id=self.business_id,
                status__in=[
                    OrderStatus.PENDING,
                    OrderStatus.PREPARING,
                    OrderStatus.READY,
                ],
            )
            .select_related("table", "cashier")
            .prefetch_related("items__menu_item", "items__modifiers__modifier_option")
            .order_by("created_at")
        )

        return OrderSerializer(orders, many=True).data

    @database_sync_to_async
    def update_order_status(self, order_id, new_status):
        """
        Update order status from kitchen display.

        Returns True if successful, False otherwise.
        """
        from apps.orders.models import Order, OrderStatus
        from apps.orders.signals import notify_kitchen_status_changed

        # Validate status value
        valid_statuses = [choice[0] for choice in OrderStatus.choices]
        if new_status not in valid_statuses:
            return False

        try:
            order = Order.all_objects.get(
                id=order_id, business_id=self.business_id
            )
            previous_status = order.status
            order.status = new_status
            order.save(update_fields=["status", "updated_at"])

            # Broadcast status change to all connected clients
            notify_kitchen_status_changed(order, previous_status=previous_status)
            return True
        except Order.DoesNotExist:
            return False
