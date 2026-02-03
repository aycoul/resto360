"""URL configuration for receipts app."""

from django.urls import path

from .views import ReceiptDownloadView

urlpatterns = [
    path(
        "orders/<uuid:order_id>/receipt/",
        ReceiptDownloadView.as_view(),
        name="receipt-download",
    ),
]
