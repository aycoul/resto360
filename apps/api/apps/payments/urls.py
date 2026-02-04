"""URL configuration for payments app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"methods", views.PaymentMethodViewSet, basename="payment-method")
router.register(r"reconciliation", views.ReconciliationView, basename="reconciliation")
router.register(
    r"drawer-sessions", views.CashDrawerSessionViewSet, basename="drawer-session"
)
# Register empty path last so it doesn't override specific paths
router.register(r"", views.PaymentViewSet, basename="payment")

urlpatterns = [
    # Webhook endpoints (no auth required)
    path("webhooks/wave/", views.WaveWebhookView.as_view(), name="webhook-wave"),
    path("webhooks/orange/", views.OrangeWebhookView.as_view(), name="webhook-orange"),
    path("webhooks/mtn/", views.MTNWebhookView.as_view(), name="webhook-mtn"),
    # Router URLs
    path("", include(router.urls)),
]
