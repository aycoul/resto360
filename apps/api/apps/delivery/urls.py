"""URL configuration for delivery API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DeliveryTrackingView,
    DeliveryViewSet,
    DeliveryZoneViewSet,
    DriverViewSet,
)

router = DefaultRouter()
router.register("zones", DeliveryZoneViewSet, basename="deliveryzone")
router.register("drivers", DriverViewSet, basename="driver")
router.register("deliveries", DeliveryViewSet, basename="delivery")

urlpatterns = [
    # Public tracking endpoint (must be before router to take precedence)
    path("track/<uuid:delivery_id>/", DeliveryTrackingView.as_view(), name="delivery-track"),
    path("", include(router.urls)),
]
