"""
URL configuration for BIZ360 project (formerly RESTO360).

The `urlpatterns` list routes URLs to views.
"""
from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    """Health check endpoint for load balancers and monitoring."""
    return JsonResponse({
        "status": "ok",
        "app": getattr(settings, "APP_NAME", "BIZ360"),
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    # Authentication (public-facing path, v1 optional)
    path("api/auth/", include("apps.authentication.urls")),
    path("api/v1/auth/", include("apps.authentication.urls")),
    # Core business apps
    path("api/v1/menu/", include("apps.menu.urls")),
    path("api/v1/", include("apps.orders.urls")),
    path("api/v1/", include("apps.receipts.urls")),
    path("api/v1/", include("apps.qr.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/ai/", include("apps.ai.urls")),
    path("api/v1/reservations/", include("apps.reservations.urls")),
    path("api/v1/reviews/", include("apps.reviews.urls")),
    path("api/v1/crm/", include("apps.crm.urls")),
    path("api/v1/website/", include("apps.website.urls")),
    path("api/v1/social/", include("apps.social.urls")),
    path("api/v1/locations/", include("apps.locations.urls")),
    path("api/v1/marketplace/", include("apps.marketplace.urls")),
    path("api/v1/financing/", include("apps.financing.urls")),
    # BIZ360 new apps
    path("api/v1/invoicing/", include("apps.invoicing.urls")),
    path("api/v1/forecasting/", include("apps.forecasting.urls")),
    path("api/v1/reorder/", include("apps.reorder.urls")),
]

# Only include delivery URLs if GIS apps are available
if not getattr(settings, "SKIP_DELIVERY_URLS", False):
    urlpatterns.append(
        path("api/v1/delivery/", include("apps.delivery.urls")),
    )
