"""WebSocket URL routing for orders app."""

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/kitchen/(?P<business_id>[0-9a-f-]+)/$",
        consumers.KitchenConsumer.as_asgi(),
    ),
]
