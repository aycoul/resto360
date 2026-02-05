"""Signal functions for broadcasting order events via WebSocket."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def notify_kitchen_order_created(order):
    """
    Notify kitchen displays of new order.

    This function calls get_channel_layer() to get the channel layer,
    then uses async_to_sync(channel_layer.group_send) to send to the
    'kitchen_{business_id}' group. The message has type 'order_created'
    which triggers KitchenConsumer.order_created() method in consumers.py.

    Args:
        order: Order instance that was created
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return  # No channel layer configured (e.g., in tests without Redis)

    from apps.orders.serializers import OrderSerializer

    async_to_sync(channel_layer.group_send)(
        f"kitchen_{order.business_id}",
        {
            "type": "order_created",  # Maps to consumer.order_created method
            "order": OrderSerializer(order).data,
        },
    )


def notify_kitchen_order_updated(order):
    """
    Notify kitchen displays of order update.

    Uses channel_layer.group_send to broadcast to kitchen_{business_id} group.
    Message type 'order_updated' triggers KitchenConsumer.order_updated().

    Args:
        order: Order instance that was updated
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    from apps.orders.serializers import OrderSerializer

    async_to_sync(channel_layer.group_send)(
        f"kitchen_{order.business_id}",
        {
            "type": "order_updated",  # Maps to consumer.order_updated method
            "order": OrderSerializer(order).data,
        },
    )


def notify_kitchen_status_changed(order, previous_status=None):
    """
    Notify kitchen displays of status change.

    Uses channel_layer.group_send to broadcast to kitchen_{business_id} group.
    Message type 'order_status_changed' triggers KitchenConsumer.order_status_changed().

    Args:
        order: Order instance with updated status
        previous_status: Previous status value (optional, for transition tracking)
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        f"kitchen_{order.business_id}",
        {
            "type": "order_status_changed",  # Maps to consumer.order_status_changed method
            "order_id": str(order.id),
            "status": order.status,
            "previous_status": previous_status,
        },
    )
