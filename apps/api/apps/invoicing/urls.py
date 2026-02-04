"""URL configuration for invoicing app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DGIConfigurationViewSet, ElectronicInvoiceViewSet

router = DefaultRouter()
router.register(r"dgi-config", DGIConfigurationViewSet, basename="dgi-config")
router.register(r"invoices", ElectronicInvoiceViewSet, basename="invoices")

urlpatterns = [
    path("", include(router.urls)),
]
