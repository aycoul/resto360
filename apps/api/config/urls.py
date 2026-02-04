"""
URL configuration for RESTO360 project.

The `urlpatterns` list routes URLs to views.
"""
from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    """Health check endpoint for load balancers and monitoring."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    # Note: /api/auth/ is the public-facing path (v1 optional)
    path("api/auth/", include("apps.authentication.urls")),
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/menu/", include("apps.menu.urls")),
    path("api/v1/", include("apps.orders.urls")),
    path("api/v1/", include("apps.receipts.urls")),
    path("api/v1/", include("apps.qr.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
]

# Only include delivery URLs if GIS apps are available
if not getattr(settings, "SKIP_DELIVERY_URLS", False):
    urlpatterns.append(
        path("api/v1/delivery/", include("apps.delivery.urls")),
    )
