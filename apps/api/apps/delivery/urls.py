"""URL configuration for delivery API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DeliveryZoneViewSet, DriverViewSet

router = DefaultRouter()
router.register("zones", DeliveryZoneViewSet, basename="deliveryzone")
router.register("drivers", DriverViewSet, basename="driver")

urlpatterns = [
    path("", include(router.urls)),
]
