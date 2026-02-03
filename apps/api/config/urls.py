"""
URL configuration for RESTO360 project.

The `urlpatterns` list routes URLs to views.
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    """Health check endpoint for load balancers and monitoring."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/menu/", include("apps.menu.urls")),
    path("api/v1/", include("apps.orders.urls")),
    path("api/v1/", include("apps.receipts.urls")),
    path("api/v1/", include("apps.qr.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
]
