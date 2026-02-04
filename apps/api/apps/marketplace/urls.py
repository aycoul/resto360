"""
URL configuration for marketplace API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CartViewSet,
    MarketplaceSearchAPI,
    SupplierCategoryViewSet,
    SupplierFavoriteViewSet,
    SupplierOrderViewSet,
    SupplierProductViewSet,
    SupplierReviewViewSet,
    SupplierViewSet,
)

router = DefaultRouter()
router.register(r"categories", SupplierCategoryViewSet, basename="supplier-category")
router.register(r"suppliers", SupplierViewSet, basename="supplier")
router.register(r"products", SupplierProductViewSet, basename="supplier-product")
router.register(r"cart", CartViewSet, basename="cart")
router.register(r"orders", SupplierOrderViewSet, basename="supplier-order")
router.register(r"reviews", SupplierReviewViewSet, basename="supplier-review")
router.register(r"favorites", SupplierFavoriteViewSet, basename="supplier-favorite")

urlpatterns = [
    path("", include(router.urls)),
    path("search/", MarketplaceSearchAPI.as_view(), name="marketplace-search"),
]
