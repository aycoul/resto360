from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActiveThemeView,
    CategoryViewSet,
    FullMenuView,
    MenuItemViewSet,
    MenuMetadataChoicesView,
    MenuThemeViewSet,
    ModifierOptionViewSet,
    ModifierViewSet,
    PublicMenuThemeView,
    PublicMenuView,
    PublicOrderCreateView,
    ThemeChoicesView,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("items", MenuItemViewSet, basename="menuitem")
router.register("modifiers", ModifierViewSet, basename="modifier")
router.register("modifier-options", ModifierOptionViewSet, basename="modifieroption")
router.register("themes", MenuThemeViewSet, basename="menutheme")

urlpatterns = [
    path("full/", FullMenuView.as_view(), name="menu-full"),
    path("metadata/choices/", MenuMetadataChoicesView.as_view(), name="menu-metadata-choices"),
    # Theme endpoints
    path("theme/active/", ActiveThemeView.as_view(), name="active-theme"),
    path("theme/choices/", ThemeChoicesView.as_view(), name="theme-choices"),
    # Public endpoints (no auth required)
    path("public/<slug:slug>/", PublicMenuView.as_view(), name="public-menu"),
    path("public/<slug:slug>/theme/", PublicMenuThemeView.as_view(), name="public-menu-theme"),
    path(
        "public/<slug:slug>/order/",
        PublicOrderCreateView.as_view(),
        name="public-order",
    ),
    path("", include(router.urls)),
]
