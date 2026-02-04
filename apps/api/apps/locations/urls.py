"""
Multi-location Support URL Configuration
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BrandAnnouncementViewSet,
    BrandDashboardView,
    BrandManagerViewSet,
    BrandViewSet,
    LocationGroupViewSet,
    LocationItemAvailabilityViewSet,
    LocationPriceOverrideViewSet,
    SharedMenuCategoryViewSet,
    SharedMenuItemViewSet,
    SharedMenuViewSet,
)

router = DefaultRouter()
router.register(r"brands", BrandViewSet, basename="brand")
router.register(r"managers", BrandManagerViewSet, basename="brand-manager")
router.register(r"groups", LocationGroupViewSet, basename="location-group")
router.register(r"shared-menus", SharedMenuViewSet, basename="shared-menu")
router.register(r"shared-categories", SharedMenuCategoryViewSet, basename="shared-category")
router.register(r"shared-items", SharedMenuItemViewSet, basename="shared-item")
router.register(r"price-overrides", LocationPriceOverrideViewSet, basename="price-override")
router.register(r"availability", LocationItemAvailabilityViewSet, basename="item-availability")
router.register(r"announcements", BrandAnnouncementViewSet, basename="announcement")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", BrandDashboardView.as_view(), name="brand-dashboard"),
]
