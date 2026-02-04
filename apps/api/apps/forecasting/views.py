"""Forecasting views for BIZ360."""

from datetime import timedelta

from django.db.models import Avg, Q, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.context import set_current_business

from .models import BusinessEvent, SalesForecast, WeatherData
from .serializers import (
    BusinessEventSerializer,
    BusinessEventWriteSerializer,
    ForecastGenerateSerializer,
    SalesForecastSerializer,
    WeatherDataSerializer,
)
from .services import ForecastService, WeatherService


class WeatherDataViewSet(viewsets.ModelViewSet):
    """ViewSet for weather data."""

    permission_classes = [IsAuthenticated]
    serializer_class = WeatherDataSerializer
    http_method_names = ["get", "post"]

    def get_queryset(self):
        set_current_business(self.request.user.business)
        return WeatherData.objects.filter(business=self.request.user.business)

    @action(detail=False, methods=["post"])
    def sync(self, request):
        """Sync weather data from API."""
        service = WeatherService()
        try:
            count = service.sync_weather_data(request.user.business)
            return Response({
                "success": True,
                "records_synced": count,
            })
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BusinessEventViewSet(viewsets.ModelViewSet):
    """ViewSet for business events."""

    permission_classes = [IsAuthenticated]
    serializer_class = BusinessEventSerializer

    def get_queryset(self):
        # Include both business-specific and global events
        return BusinessEvent.objects.filter(
            Q(business=self.request.user.business) | Q(business__isnull=True)
        ).order_by("date")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return BusinessEventWriteSerializer
        return BusinessEventSerializer

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Get upcoming events for the next 30 days."""
        today = timezone.localdate()
        end_date = today + timedelta(days=30)

        events = self.get_queryset().filter(
            Q(date__gte=today, date__lte=end_date) |
            Q(date__lte=today, end_date__gte=today)
        )
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)


class SalesForecastViewSet(viewsets.ModelViewSet):
    """ViewSet for sales forecasts."""

    permission_classes = [IsAuthenticated]
    serializer_class = SalesForecastSerializer
    http_method_names = ["get", "post"]

    def get_queryset(self):
        set_current_business(self.request.user.business)
        return SalesForecast.objects.filter(
            business=self.request.user.business
        ).order_by("forecast_date")

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate forecasts for upcoming days."""
        serializer = ForecastGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        days = serializer.validated_data["days"]
        service = ForecastService(request.user.business)
        forecasts = service.generate_forecasts(days)

        output = SalesForecastSerializer(forecasts, many=True)
        return Response({
            "success": True,
            "forecasts": output.data,
        })

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        """Get forecast dashboard data."""
        today = timezone.localdate()
        end_date = today + timedelta(days=7)

        # Get or generate forecasts
        service = ForecastService(request.user.business)
        forecasts = []
        for i in range(7):
            target_date = today + timedelta(days=i)
            try:
                forecast = SalesForecast.objects.get(
                    business=request.user.business,
                    forecast_date=target_date,
                )
            except SalesForecast.DoesNotExist:
                forecast = service.generate_forecast(target_date)
            forecasts.append(forecast)

        # Calculate summary
        total_revenue = sum(f.predicted_revenue for f in forecasts)
        total_orders = sum(f.predicted_order_count for f in forecasts)
        avg_confidence = sum(f.confidence_score for f in forecasts) / len(forecasts) if forecasts else 0

        # Get upcoming events
        events = BusinessEvent.objects.filter(
            Q(business=request.user.business) | Q(business__isnull=True),
            Q(date__gte=today, date__lte=end_date) |
            Q(date__lte=today, end_date__gte=today)
        )

        return Response({
            "total_predicted_revenue": total_revenue,
            "total_predicted_orders": total_orders,
            "avg_confidence": float(avg_confidence),
            "forecasts": SalesForecastSerializer(forecasts, many=True).data,
            "upcoming_events": BusinessEventSerializer(events, many=True).data,
        })

    @action(detail=False, methods=["post"])
    def update_actuals(self, request):
        """Update forecasts with actual results for past dates."""
        service = ForecastService(request.user.business)
        today = timezone.localdate()
        updated = 0

        # Update actuals for the past 7 days
        for i in range(1, 8):
            past_date = today - timedelta(days=i)
            forecast = service.update_actual_results(past_date)
            if forecast and forecast.actual_revenue is not None:
                updated += 1

        return Response({
            "success": True,
            "updated_count": updated,
        })

    @action(detail=False, methods=["get"])
    def accuracy_report(self, request):
        """Get accuracy report for past forecasts."""
        today = timezone.localdate()
        start_date = today - timedelta(days=30)

        forecasts = SalesForecast.objects.filter(
            business=request.user.business,
            forecast_date__gte=start_date,
            forecast_date__lt=today,
            actual_revenue__isnull=False,
        )

        avg_accuracy = forecasts.aggregate(avg=Avg("accuracy_score"))["avg"]

        return Response({
            "period_start": start_date,
            "period_end": today,
            "total_forecasts": forecasts.count(),
            "average_accuracy": float(avg_accuracy) if avg_accuracy else None,
            "forecasts": SalesForecastSerializer(forecasts, many=True).data,
        })
