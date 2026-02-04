"""URL configuration for reorder app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomerOrderHistoryViewSet,
    PublicReorderView,
    ReorderQRCodeViewSet,
    ReorderScanViewSet,
)

router = DefaultRouter()
router.register(r"qr-codes", ReorderQRCodeViewSet, basename="qr-codes")
router.register(r"scans", ReorderScanViewSet, basename="scans")

urlpatterns = [
    path("", include(router.urls)),
    # Public endpoints (no auth)
    path(
        "public/<uuid:code>/",
        PublicReorderView.as_view({"get": "retrieve"}),
        name="public-reorder-info",
    ),
    path(
        "public/<uuid:code>/submit/",
        PublicReorderView.as_view({"post": "submit"}),
        name="public-reorder-submit",
    ),
    # Customer history (public, requires phone)
    path(
        "history/lookup/",
        CustomerOrderHistoryViewSet.as_view({"post": "lookup"}),
        name="customer-lookup",
    ),
    path(
        "history/detail/",
        CustomerOrderHistoryViewSet.as_view({"get": "order_detail"}),
        name="customer-order-detail",
    ),
    path(
        "history/reorder/",
        CustomerOrderHistoryViewSet.as_view({"post": "reorder"}),
        name="customer-reorder",
    ),
]
