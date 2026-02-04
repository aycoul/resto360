"""WebSocket URL routing for delivery."""

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/driver/(?P<driver_id>[0-9a-f-]+)/location/$",
        consumers.DriverLocationConsumer.as_asgi(),
    ),
    re_path(
        r"ws/delivery/(?P<delivery_id>[0-9a-f-]+)/track/$",
        consumers.DeliveryTrackingConsumer.as_asgi(),
    ),
]
