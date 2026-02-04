from django.contrib import admin

from .models import BusinessEvent, SalesForecast, WeatherData


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = [
        "business",
        "date",
        "weather_condition",
        "temperature_high",
        "temperature_low",
        "precipitation_mm",
    ]
    list_filter = ["weather_condition", "date"]
    search_fields = ["business__name"]
    date_hierarchy = "date"


@admin.register(BusinessEvent)
class BusinessEventAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "event_type",
        "date",
        "expected_impact",
        "is_recurring",
        "business",
    ]
    list_filter = ["event_type", "expected_impact", "is_recurring", "date"]
    search_fields = ["name", "description"]
    date_hierarchy = "date"


@admin.register(SalesForecast)
class SalesForecastAdmin(admin.ModelAdmin):
    list_display = [
        "business",
        "forecast_date",
        "predicted_revenue",
        "actual_revenue",
        "accuracy_score",
        "confidence_level",
    ]
    list_filter = ["confidence_level", "forecast_date"]
    search_fields = ["business__name"]
    date_hierarchy = "forecast_date"
    readonly_fields = ["factors", "generated_at"]
