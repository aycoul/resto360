"""Forecasting serializers for BIZ360."""

from rest_framework import serializers

from .models import BusinessEvent, SalesForecast, WeatherData


class WeatherDataSerializer(serializers.ModelSerializer):
    """Serializer for weather data."""

    condition_display = serializers.CharField(source="get_weather_condition_display", read_only=True)

    class Meta:
        model = WeatherData
        fields = [
            "id",
            "date",
            "temperature_high",
            "temperature_low",
            "temperature_avg",
            "precipitation_mm",
            "precipitation_probability",
            "weather_condition",
            "condition_display",
            "humidity_percent",
            "wind_speed_kmh",
            "source",
            "fetched_at",
        ]
        read_only_fields = ["id", "source", "fetched_at"]


class BusinessEventSerializer(serializers.ModelSerializer):
    """Serializer for business events."""

    event_type_display = serializers.CharField(source="get_event_type_display", read_only=True)
    impact_display = serializers.CharField(source="get_expected_impact_display", read_only=True)

    class Meta:
        model = BusinessEvent
        fields = [
            "id",
            "name",
            "description",
            "event_type",
            "event_type_display",
            "date",
            "end_date",
            "expected_impact",
            "impact_display",
            "impact_factor",
            "is_recurring",
            "recurrence_pattern",
            "applies_to_region",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BusinessEventWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating business events."""

    class Meta:
        model = BusinessEvent
        fields = [
            "name",
            "description",
            "event_type",
            "date",
            "end_date",
            "expected_impact",
            "impact_factor",
            "is_recurring",
            "recurrence_pattern",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request.user, "business"):
            validated_data["business"] = request.user.business
        return super().create(validated_data)


class SalesForecastSerializer(serializers.ModelSerializer):
    """Serializer for sales forecasts."""

    accuracy_percentage = serializers.SerializerMethodField()

    class Meta:
        model = SalesForecast
        fields = [
            "id",
            "forecast_date",
            "generated_at",
            "predicted_revenue",
            "predicted_order_count",
            "predicted_avg_order_value",
            "confidence_score",
            "confidence_level",
            "factors",
            "actual_revenue",
            "actual_order_count",
            "actual_avg_order_value",
            "accuracy_score",
            "accuracy_percentage",
        ]
        read_only_fields = [
            "id", "generated_at", "confidence_score", "confidence_level",
            "factors", "accuracy_score",
        ]

    def get_accuracy_percentage(self, obj):
        if obj.accuracy_score is not None:
            return f"{obj.accuracy_score:.1f}%"
        return None


class ForecastGenerateSerializer(serializers.Serializer):
    """Serializer for generating forecasts."""

    days = serializers.IntegerField(min_value=1, max_value=30, default=7)


class ForecastSummarySerializer(serializers.Serializer):
    """Summary serializer for forecast dashboard."""

    total_predicted_revenue = serializers.IntegerField()
    total_predicted_orders = serializers.IntegerField()
    avg_confidence = serializers.DecimalField(max_digits=3, decimal_places=2)
    forecasts = SalesForecastSerializer(many=True)
    upcoming_events = BusinessEventSerializer(many=True)
