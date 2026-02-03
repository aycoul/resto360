from rest_framework.routers import DefaultRouter

from .views import (
    MenuItemIngredientViewSet,
    ReportViewSet,
    StockItemViewSet,
    StockMovementViewSet,
)

router = DefaultRouter()
router.register("stock-items", StockItemViewSet, basename="stock-item")
router.register("movements", StockMovementViewSet, basename="stock-movement")
router.register("recipes", MenuItemIngredientViewSet, basename="recipe")
router.register("reports", ReportViewSet, basename="report")

urlpatterns = router.urls
