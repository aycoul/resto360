"""URL configuration for forecasting app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BusinessEventViewSet, SalesForecastViewSet, WeatherDataViewSet

router = DefaultRouter()
router.register(r"weather", WeatherDataViewSet, basename="weather")
router.register(r"events", BusinessEventViewSet, basename="events")
router.register(r"forecasts", SalesForecastViewSet, basename="forecasts")

urlpatterns = [
    path("", include(router.urls)),
]
