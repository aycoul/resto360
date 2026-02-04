"""
Sales Forecasting Service for BIZ360.

Generates sales forecasts using historical data, weather conditions, and events.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from django.db.models import Avg, Sum, Q
from django.utils import timezone

from apps.analytics.models import DailySalesStats
from apps.orders.models import Order, OrderStatus

from ..models import (
    BusinessEvent,
    BusinessEventImpact,
    SalesForecast,
    WeatherData,
)

logger = logging.getLogger(__name__)


class ForecastService:
    """Service for generating sales forecasts."""

    # Number of weeks of historical data to use
    HISTORICAL_WEEKS = 8

    def __init__(self, business):
        """
        Initialize forecast service for a business.

        Args:
            business: Business instance
        """
        self.business = business

    def generate_forecast(self, target_date: date) -> SalesForecast:
        """
        Generate sales forecast for a specific date.

        Args:
            target_date: Date to forecast

        Returns:
            SalesForecast: Generated forecast
        """
        # 1. Get historical baseline (same day of week, last N weeks)
        historical_avg = self._get_historical_average(target_date)

        # 2. Day of week factor
        dow_factor = self._get_day_of_week_factor(target_date)

        # 3. Weather factor
        weather_factor = self._get_weather_factor(target_date)

        # 4. Event factor (holidays, local events)
        event_factor, events = self._get_event_factor(target_date)

        # 5. Trend factor (growth/decline over time)
        trend_factor = self._get_trend_factor()

        # Calculate prediction
        base_revenue = historical_avg if historical_avg > 0 else self._get_overall_average()
        predicted_revenue = int(
            Decimal(str(base_revenue))
            * dow_factor
            * weather_factor
            * event_factor
            * trend_factor
        )

        # Calculate predicted order count
        avg_order_value = self._get_average_order_value()
        predicted_orders = max(1, int(predicted_revenue / avg_order_value)) if avg_order_value > 0 else 0

        # Confidence based on data availability
        confidence = self._calculate_confidence(target_date, historical_avg)

        # Determine confidence level
        if confidence >= 0.7:
            confidence_level = "high"
        elif confidence >= 0.4:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        # Create or update forecast
        forecast, _ = SalesForecast.objects.update_or_create(
            business=self.business,
            forecast_date=target_date,
            defaults={
                "predicted_revenue": max(0, predicted_revenue),
                "predicted_order_count": max(0, predicted_orders),
                "predicted_avg_order_value": avg_order_value,
                "confidence_score": confidence,
                "confidence_level": confidence_level,
                "factors": {
                    "historical_avg": float(historical_avg),
                    "day_of_week_factor": float(dow_factor),
                    "weather_factor": float(weather_factor),
                    "event_factor": float(event_factor),
                    "trend_factor": float(trend_factor),
                    "events": events,
                    "avg_order_value": float(avg_order_value),
                },
            }
        )

        return forecast

    def generate_forecasts(self, days: int = 7) -> List[SalesForecast]:
        """
        Generate forecasts for the next N days.

        Args:
            days: Number of days to forecast

        Returns:
            List[SalesForecast]: Generated forecasts
        """
        forecasts = []
        today = timezone.localdate()

        for i in range(days):
            target_date = today + timedelta(days=i)
            forecast = self.generate_forecast(target_date)
            forecasts.append(forecast)

        return forecasts

    def update_actual_results(self, target_date: date) -> Optional[SalesForecast]:
        """
        Update forecast with actual results after the day has passed.

        Args:
            target_date: Date to update

        Returns:
            SalesForecast or None if not found
        """
        try:
            forecast = SalesForecast.objects.get(
                business=self.business,
                forecast_date=target_date,
            )
        except SalesForecast.DoesNotExist:
            return None

        # Get actual results from orders
        actual_data = Order.objects.filter(
            business=self.business,
            created_at__date=target_date,
            status=OrderStatus.COMPLETED,
        ).aggregate(
            total_revenue=Sum("total"),
            order_count=Sum("id"),
        )

        actual_revenue = actual_data["total_revenue"] or 0
        actual_count = Order.objects.filter(
            business=self.business,
            created_at__date=target_date,
            status=OrderStatus.COMPLETED,
        ).count()

        forecast.actual_revenue = actual_revenue
        forecast.actual_order_count = actual_count
        forecast.actual_avg_order_value = (
            int(actual_revenue / actual_count) if actual_count > 0 else 0
        )
        forecast.calculate_accuracy()
        forecast.save()

        return forecast

    def _get_historical_average(self, target_date: date) -> Decimal:
        """Get average revenue for same day of week over past weeks."""
        day_of_week = target_date.weekday()
        lookback_dates = []

        for week in range(1, self.HISTORICAL_WEEKS + 1):
            past_date = target_date - timedelta(weeks=week)
            lookback_dates.append(past_date)

        # Try DailySalesStats first
        stats = DailySalesStats.objects.filter(
            business=self.business,
            date__in=lookback_dates,
        ).aggregate(avg_revenue=Avg("total_revenue"))

        if stats["avg_revenue"]:
            return Decimal(str(stats["avg_revenue"]))

        # Fall back to Order aggregation
        orders = Order.objects.filter(
            business=self.business,
            created_at__date__in=lookback_dates,
            status=OrderStatus.COMPLETED,
        ).aggregate(avg_total=Avg("total"))

        return Decimal(str(orders["avg_total"] or 0))

    def _get_overall_average(self) -> Decimal:
        """Get overall daily average revenue."""
        stats = DailySalesStats.objects.filter(
            business=self.business,
        ).aggregate(avg_revenue=Avg("total_revenue"))

        if stats["avg_revenue"]:
            return Decimal(str(stats["avg_revenue"]))

        # Default fallback
        return Decimal("50000")  # 50,000 XOF default

    def _get_day_of_week_factor(self, target_date: date) -> Decimal:
        """Get factor based on day of week performance."""
        day_of_week = target_date.weekday()

        # Get average by day of week
        day_avg = DailySalesStats.objects.filter(
            business=self.business,
            date__week_day=day_of_week + 2,  # Django week_day: 1=Sunday
        ).aggregate(avg=Avg("total_revenue"))

        overall_avg = DailySalesStats.objects.filter(
            business=self.business,
        ).aggregate(avg=Avg("total_revenue"))

        if day_avg["avg"] and overall_avg["avg"] and overall_avg["avg"] > 0:
            return Decimal(str(day_avg["avg"])) / Decimal(str(overall_avg["avg"]))

        # Default day-of-week factors for West Africa
        default_factors = {
            0: Decimal("0.85"),   # Monday - typically slower
            1: Decimal("0.90"),   # Tuesday
            2: Decimal("1.00"),   # Wednesday
            3: Decimal("1.05"),   # Thursday
            4: Decimal("1.30"),   # Friday - payday, social events
            5: Decimal("1.40"),   # Saturday - peak
            6: Decimal("1.20"),   # Sunday - family dining
        }
        return default_factors.get(day_of_week, Decimal("1.0"))

    def _get_weather_factor(self, target_date: date) -> Decimal:
        """Get weather impact factor."""
        try:
            weather = WeatherData.objects.get(
                business=self.business,
                date=target_date,
            )
        except WeatherData.DoesNotExist:
            return Decimal("1.0")  # Neutral if no data

        # Weather impact logic
        factor = Decimal("1.0")

        # Rain impact
        if weather.weather_condition == "rainy":
            factor *= Decimal("0.85")  # 15% drop
        elif weather.weather_condition == "stormy":
            factor *= Decimal("0.70")  # 30% drop
        elif weather.precipitation_mm > 10:
            factor *= Decimal("0.90")

        # Extreme heat impact
        if weather.temperature_high > 38:
            factor *= Decimal("0.92")  # Very hot
        elif weather.temperature_high > 35:
            factor *= Decimal("0.95")

        # Harmattan (dry dusty season)
        if weather.weather_condition == "harmattan":
            factor *= Decimal("0.95")

        return factor

    def _get_event_factor(self, target_date: date) -> tuple:
        """Get event impact factor and list of events."""
        events = BusinessEvent.objects.filter(
            Q(business=self.business) | Q(business__isnull=True),
            Q(date=target_date) | Q(date__lte=target_date, end_date__gte=target_date),
        )

        factor = Decimal("1.0")
        event_names = []

        for event in events:
            event_names.append(event.name)

            # Use stored impact_factor if available
            if event.impact_factor != Decimal("1.0"):
                factor *= event.impact_factor
            else:
                # Map expected_impact to factor
                impact_map = {
                    BusinessEventImpact.VERY_POSITIVE: Decimal("1.50"),
                    BusinessEventImpact.POSITIVE: Decimal("1.25"),
                    BusinessEventImpact.NEUTRAL: Decimal("1.00"),
                    BusinessEventImpact.NEGATIVE: Decimal("0.75"),
                    BusinessEventImpact.VERY_NEGATIVE: Decimal("0.50"),
                }
                factor *= impact_map.get(event.expected_impact, Decimal("1.0"))

        return factor, event_names

    def _get_trend_factor(self) -> Decimal:
        """Calculate trend factor based on recent performance vs historical."""
        # Compare last 2 weeks to previous 6 weeks
        today = timezone.localdate()
        recent_start = today - timedelta(weeks=2)
        historical_end = recent_start - timedelta(days=1)
        historical_start = historical_end - timedelta(weeks=6)

        recent_avg = DailySalesStats.objects.filter(
            business=self.business,
            date__gte=recent_start,
            date__lt=today,
        ).aggregate(avg=Avg("total_revenue"))

        historical_avg = DailySalesStats.objects.filter(
            business=self.business,
            date__gte=historical_start,
            date__lt=historical_end,
        ).aggregate(avg=Avg("total_revenue"))

        if recent_avg["avg"] and historical_avg["avg"] and historical_avg["avg"] > 0:
            trend = Decimal(str(recent_avg["avg"])) / Decimal(str(historical_avg["avg"]))
            # Cap trend factor between 0.8 and 1.2
            return max(Decimal("0.8"), min(Decimal("1.2"), trend))

        return Decimal("1.0")

    def _get_average_order_value(self) -> int:
        """Get average order value."""
        avg = Order.objects.filter(
            business=self.business,
            status=OrderStatus.COMPLETED,
        ).aggregate(avg=Avg("total"))

        return int(avg["avg"] or 5000)  # Default 5000 XOF

    def _calculate_confidence(self, target_date: date, historical_avg: Decimal) -> Decimal:
        """Calculate confidence score based on data availability."""
        score = Decimal("0.0")

        # Historical data (max 0.4)
        if historical_avg > 0:
            weeks_with_data = DailySalesStats.objects.filter(
                business=self.business,
                date__gte=target_date - timedelta(weeks=self.HISTORICAL_WEEKS),
            ).count()
            score += Decimal(str(min(0.4, weeks_with_data / (self.HISTORICAL_WEEKS * 7) * 0.4)))

        # Weather data (max 0.2)
        has_weather = WeatherData.objects.filter(
            business=self.business,
            date=target_date,
        ).exists()
        if has_weather:
            score += Decimal("0.2")

        # Days until forecast (max 0.3 - higher for nearer dates)
        days_until = (target_date - timezone.localdate()).days
        if days_until <= 1:
            score += Decimal("0.3")
        elif days_until <= 3:
            score += Decimal("0.2")
        elif days_until <= 7:
            score += Decimal("0.1")

        # Event data considered (max 0.1)
        has_events = BusinessEvent.objects.filter(
            Q(business=self.business) | Q(business__isnull=True),
            date=target_date,
        ).exists()
        if has_events:
            score += Decimal("0.1")

        return min(Decimal("1.0"), score)
