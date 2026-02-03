from rest_framework.routers import DefaultRouter

from .views import MenuItemIngredientViewSet, StockItemViewSet, StockMovementViewSet

router = DefaultRouter()
router.register("stock-items", StockItemViewSet, basename="stock-item")
router.register("movements", StockMovementViewSet, basename="stock-movement")
router.register("recipes", MenuItemIngredientViewSet, basename="recipe")

urlpatterns = router.urls
