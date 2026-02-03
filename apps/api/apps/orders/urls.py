"""URL configuration for orders app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import KitchenQueueView, OrderViewSet, TableViewSet

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="order")
router.register("tables", TableViewSet, basename="table")

urlpatterns = [
    path("kitchen-queue/", KitchenQueueView.as_view(), name="kitchen-queue"),
    path("", include(router.urls)),
]
