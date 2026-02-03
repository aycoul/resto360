"""URL configuration for qr app."""

from django.urls import path

from .views import MenuQRCodeView

urlpatterns = [
    path("menu-qr/", MenuQRCodeView.as_view(), name="menu-qr"),
]
