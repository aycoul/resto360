"""URL configuration for payments app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"methods", views.PaymentMethodViewSet, basename="payment-method")
router.register(
    r"drawer-sessions", views.CashDrawerSessionViewSet, basename="drawer-session"
)

urlpatterns = [
    path("", include(router.urls)),
]
