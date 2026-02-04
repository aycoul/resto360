"""
Forecasting models for BIZ360.

Sales forecasting using historical data, weather conditions, and events.
Designed for West African market with focus on Ivory Coast.
"""

from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.core.managers import TenantManager
from apps.core.models import BaseModel, TenantModel


class WeatherData(TenantModel):
    """Daily weather data for forecasting correlation."""

    WEATHER_CONDITIONS = [
        ("sunny", "Sunny"),
        ("partly_cloudy", "Partly Cloudy"),
        ("cloudy", "Cloudy"),
        ("rainy", "Rainy"),
        ("stormy", "Stormy"),
        ("harmattan", "Harmattan"),  # West African dry dusty wind
    ]

    date = models.DateField()

    # Temperature (Celsius)
    temperature_high = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Highest temperature of the day (°C)",
    )
    temperature_low = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Lowest temperature of the day (°C)",
    )
    temperature_avg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average temperature (°C)",
    )

    # Precipitation
    precipitation_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Precipitation in millimeters",
    )
    precipitation_probability = models.IntegerField(
        default=0,
        help_text="Probability of precipitation (0-100%)",
    )

    # Conditions
    weather_condition = models.CharField(
        max_length=20,
        choices=WEATHER_CONDITIONS,
        default="sunny",
    )
    humidity_percent = models.IntegerField(
        default=0,
        help_text="Humidity percentage (0-100)",
    )
    wind_speed_kmh = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Wind speed in km/h",
    )

    # Source tracking
    source = models.CharField(
        max_length=50,
        default="openweathermap",
        help_text="Data source (e.g., openweathermap, manual)",
    )
    fetched_at = models.DateTimeField(null=True, blank=True)

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-date"]
        unique_together = ["business", "date"]
        verbose_name = "Weather Data"
        verbose_name_plural = "Weather Data"
        indexes = [
            models.Index(fields=["business", "date"]),
        ]

    def __str__(self):
        return f"{self.business.name} - {self.date}: {self.weather_condition}"


class BusinessEventType(models.TextChoices):
    """Types of events that impact business."""

    NATIONAL_HOLIDAY = "national_holiday", "National Holiday"
    RELIGIOUS_HOLIDAY = "religious_holiday", "Religious Holiday"
    LOCAL_EVENT = "local_event", "Local Event"
    PROMOTION = "promotion", "Promotion/Sale"
    COMPETITION = "competition", "Competition Event"
    SCHOOL_HOLIDAY = "school_holiday", "School Holiday"
    SPORTS_EVENT = "sports_event", "Sports Event"
    CUSTOM = "custom", "Custom Event"


class BusinessEventImpact(models.TextChoices):
    """Expected impact on sales."""

    VERY_POSITIVE = "very_positive", "+50% or more"
    POSITIVE = "positive", "+10-50%"
    NEUTRAL = "neutral", "No impact"
    NEGATIVE = "negative", "-10-50%"
    VERY_NEGATIVE = "very_negative", "-50% or more"


class BusinessEvent(BaseModel):
    """Events that impact sales (holidays, local events, etc.)."""

    # Scope - null business means it applies to all businesses (global event)
    business = models.ForeignKey(
        "authentication.Business",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="business_events",
        help_text="Leave empty for global events (holidays)",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(
        max_length=20,
        choices=BusinessEventType.choices,
    )
    date = models.DateField()
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date for multi-day events",
    )

    # Impact estimation
    expected_impact = models.CharField(
        max_length=20,
        choices=BusinessEventImpact.choices,
        default=BusinessEventImpact.NEUTRAL,
    )
    impact_factor = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.00,
        help_text="Multiplier for sales forecast (e.g., 1.5 = +50%)",
    )

    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ("yearly", "Yearly (same date)"),
            ("yearly_weekday", "Yearly (same weekday)"),
            ("monthly", "Monthly"),
            ("islamic", "Islamic Calendar"),
        ],
        help_text="Pattern for recurring events",
    )

    # Region applicability (for global events)
    applies_to_region = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Region code (e.g., 'CI' for Ivory Coast)",
    )

    class Meta:
        ordering = ["date"]
        verbose_name = "Business Event"
        verbose_name_plural = "Business Events"
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["business", "date"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.date}"


class SalesForecast(TenantModel):
    """Generated sales forecasts."""

    forecast_date = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)

    # Predictions
    predicted_revenue = models.PositiveIntegerField(
        help_text="Predicted revenue in XOF",
    )
    predicted_order_count = models.PositiveIntegerField(
        help_text="Predicted number of orders",
    )
    predicted_avg_order_value = models.PositiveIntegerField(
        default=0,
        help_text="Predicted average order value",
    )

    # Confidence
    confidence_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        help_text="Confidence score (0.00-1.00)",
    )
    confidence_level = models.CharField(
        max_length=10,
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        default="medium",
    )

    # Factors considered (stored for transparency)
    factors = models.JSONField(
        default=dict,
        help_text="Breakdown of factors used in forecast",
    )
    # Example:
    # {
    #   "historical_avg": 150000,
    #   "day_of_week_factor": 1.2,
    #   "weather_factor": 0.9,
    #   "event_factor": 1.3,
    #   "trend_factor": 1.05,
    #   "events": ["Independence Day"]
    # }

    # Actual vs predicted (filled after the day passes)
    actual_revenue = models.PositiveIntegerField(null=True, blank=True)
    actual_order_count = models.PositiveIntegerField(null=True, blank=True)
    actual_avg_order_value = models.PositiveIntegerField(null=True, blank=True)
    accuracy_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Accuracy percentage (actual vs predicted)",
    )

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-forecast_date"]
        unique_together = ["business", "forecast_date"]
        verbose_name = "Sales Forecast"
        verbose_name_plural = "Sales Forecasts"
        indexes = [
            models.Index(fields=["business", "forecast_date"]),
        ]

    def __str__(self):
        return f"{self.business.name} - {self.forecast_date}: {self.predicted_revenue} XOF"

    def calculate_accuracy(self):
        """Calculate accuracy after actual results are known."""
        if self.actual_revenue is not None and self.predicted_revenue > 0:
            diff = abs(self.actual_revenue - self.predicted_revenue)
            self.accuracy_score = max(0, 100 - (diff / self.predicted_revenue * 100))
            return self.accuracy_score
        return None
