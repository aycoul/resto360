from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    FullMenuView,
    MenuItemViewSet,
    ModifierOptionViewSet,
    ModifierViewSet,
    PublicMenuView,
    PublicOrderCreateView,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("items", MenuItemViewSet, basename="menuitem")
router.register("modifiers", ModifierViewSet, basename="modifier")
router.register("modifier-options", ModifierOptionViewSet, basename="modifieroption")

urlpatterns = [
    path("full/", FullMenuView.as_view(), name="menu-full"),
    # Public endpoints (no auth required)
    path("public/<slug:slug>/", PublicMenuView.as_view(), name="public-menu"),
    path(
        "public/<slug:slug>/order/",
        PublicOrderCreateView.as_view(),
        name="public-order",
    ),
    path("", include(router.urls)),
]
