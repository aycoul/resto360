"""WebSocket consumers for delivery tracking."""

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone


class DriverLocationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket for driver location updates.

    Driver connects and sends location updates.
    System broadcasts to all subscribers (kitchen, customer tracking).

    URL: /ws/driver/{driver_id}/location/?token={jwt}
    """

    async def connect(self):
        """Handle WebSocket connection."""
        # Get user from JWT middleware
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)  # Not authenticated
            return

        self.driver_id = self.scope["url_route"]["kwargs"]["driver_id"]

        # Verify user is this driver
        is_valid = await self.verify_driver_ownership()
        if not is_valid:
            await self.close(code=4003)  # Not authorized
            return

        # Join driver location group
        self.group_name = f"driver_location_{self.driver_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        """Handle incoming messages from driver."""
        msg_type = content.get("type")

        if msg_type == "location_update":
            lat = content.get("lat")
            lng = content.get("lng")
            accuracy = content.get("accuracy")
            heading = content.get("heading")
            speed = content.get("speed")

            if lat is not None and lng is not None:
                # Save to database
                await self.save_driver_location(lat, lng)

                # Broadcast to all subscribers
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "driver_location",
                        "driver_id": self.driver_id,
                        "lat": lat,
                        "lng": lng,
                        "accuracy": accuracy,
                        "heading": heading,
                        "speed": speed,
                        "timestamp": timezone.now().isoformat(),
                    },
                )

    async def driver_location(self, event):
        """Send location update to subscriber."""
        await self.send_json(
            {
                "type": "location",
                "driver_id": event["driver_id"],
                "lat": event["lat"],
                "lng": event["lng"],
                "accuracy": event.get("accuracy"),
                "heading": event.get("heading"),
                "speed": event.get("speed"),
                "timestamp": event["timestamp"],
            }
        )

    async def delivery_status_update(self, event):
        """Send delivery status update to subscribers."""
        await self.send_json(
            {
                "type": "status_update",
                "status": event["status"],
                "timestamp": event["timestamp"],
            }
        )

    @database_sync_to_async
    def verify_driver_ownership(self) -> bool:
        """Verify user owns this driver profile."""
        from apps.delivery.models import Driver

        try:
            driver = Driver.all_objects.get(id=self.driver_id)
            return str(driver.user_id) == str(self.user.id)
        except Driver.DoesNotExist:
            return False

    @database_sync_to_async
    def save_driver_location(self, lat: float, lng: float):
        """Save driver location to database."""
        from apps.delivery.models import Driver

        try:
            driver = Driver.all_objects.get(id=self.driver_id)
            driver.update_location(lat, lng)
        except Driver.DoesNotExist:
            pass


class DeliveryTrackingConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket for customers tracking their delivery.

    Subscribes to driver location for a specific delivery.

    URL: /ws/delivery/{delivery_id}/track/?token={jwt}
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.delivery_id = self.scope["url_route"]["kwargs"]["delivery_id"]

        # For customer tracking, we allow anonymous access with delivery ID
        # In production, you may want to add phone number verification
        delivery_info = await self.get_delivery_info()
        if not delivery_info:
            await self.close(code=4004)  # Delivery not found
            return

        self.driver_id = delivery_info.get("driver_id")

        await self.accept()

        # Send initial delivery state
        await self.send_json({"type": "delivery_info", "delivery": delivery_info})

        # Subscribe to driver location if driver is assigned
        if self.driver_id:
            self.group_name = f"driver_location_{self.driver_id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def driver_location(self, event):
        """Forward driver location to customer."""
        await self.send_json(
            {
                "type": "driver_location",
                "lat": event["lat"],
                "lng": event["lng"],
                "heading": event.get("heading"),
                "timestamp": event["timestamp"],
            }
        )

    async def delivery_status_update(self, event):
        """Send delivery status update to customer."""
        await self.send_json(
            {
                "type": "status_update",
                "status": event["status"],
                "timestamp": event["timestamp"],
            }
        )

    @database_sync_to_async
    def get_delivery_info(self) -> dict:
        """Get delivery information."""
        from apps.delivery.models import Delivery

        try:
            delivery = Delivery.all_objects.select_related(
                "driver", "driver__user"
            ).get(id=self.delivery_id)

            info = {
                "id": str(delivery.id),
                "status": delivery.status,
                "delivery_address": delivery.delivery_address,
                "estimated_delivery_time": (
                    delivery.estimated_delivery_time.isoformat()
                    if delivery.estimated_delivery_time
                    else None
                ),
                "driver_id": str(delivery.driver_id) if delivery.driver_id else None,
            }

            if delivery.driver:
                info["driver"] = {
                    "name": delivery.driver.user.name,
                    "phone": delivery.driver.phone,
                    "vehicle_type": delivery.driver.vehicle_type,
                }
                if delivery.driver.current_location:
                    info["driver"]["lat"] = delivery.driver.current_location.y
                    info["driver"]["lng"] = delivery.driver.current_location.x

            return info
        except Delivery.DoesNotExist:
            return None


# Signal functions for broadcasting status updates
async def broadcast_delivery_status(delivery_id: str, status: str):
    """Broadcast delivery status update to tracking subscribers."""
    from channels.layers import get_channel_layer

    from apps.delivery.models import Delivery

    channel_layer = get_channel_layer()

    # Get driver ID for this delivery to find the right group
    try:
        delivery = Delivery.all_objects.get(id=delivery_id)
        if delivery.driver_id:
            group_name = f"driver_location_{delivery.driver_id}"
            await channel_layer.group_send(
                group_name,
                {
                    "type": "delivery_status_update",
                    "status": status,
                    "timestamp": timezone.now().isoformat(),
                },
            )
    except Delivery.DoesNotExist:
        pass
