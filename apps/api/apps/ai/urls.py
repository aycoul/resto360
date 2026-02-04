"""URL configuration for AI app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AIJobViewSet,
    AIUsageView,
    BulkImportView,
    GenerateDescriptionView,
    ImportConfirmView,
    MenuImportBatchViewSet,
    MenuOCRView,
    PhotoAnalysisView,
    PriceSuggestionView,
    TranslateItemView,
    TranslateMenuView,
)

router = DefaultRouter()
router.register("jobs", AIJobViewSet, basename="ai-job")
router.register("imports", MenuImportBatchViewSet, basename="menu-import")

urlpatterns = [
    # AI generation endpoints
    path("generate/description/", GenerateDescriptionView.as_view(), name="ai-generate-description"),
    path("generate/price/", PriceSuggestionView.as_view(), name="ai-suggest-price"),

    # Photo analysis
    path("photo/analyze/", PhotoAnalysisView.as_view(), name="ai-photo-analyze"),

    # Menu OCR
    path("ocr/menu/", MenuOCRView.as_view(), name="ai-menu-ocr"),

    # Bulk import
    path("import/file/", BulkImportView.as_view(), name="ai-bulk-import"),
    path("import/<uuid:batch_id>/confirm/", ImportConfirmView.as_view(), name="ai-import-confirm"),

    # Translation
    path("translate/item/", TranslateItemView.as_view(), name="ai-translate-item"),
    path("translate/menu/", TranslateMenuView.as_view(), name="ai-translate-menu"),

    # Usage tracking
    path("usage/", AIUsageView.as_view(), name="ai-usage"),

    # Router URLs
    path("", include(router.urls)),
]
