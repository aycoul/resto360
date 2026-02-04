"""Serializers for delivery API."""

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import DeliveryZone, Driver


class DeliveryZoneSerializer(GeoFeatureModelSerializer):
    """
    Serialize DeliveryZone as GeoJSON Feature.

    Output format:
    {
      "type": "Feature",
      "geometry": { "type": "Polygon", "coordinates": [...] },
      "properties": { "id": "...", "name": "Zone A", ... }
    }
    """

    class Meta:
        model = DeliveryZone
        geo_field = "polygon"
        id_field = "id"
        fields = [
            "id",
            "name",
            "delivery_fee",
            "minimum_order",
            "estimated_time_minutes",
            "is_active",
            "created_at",
            "updated_at",
        ]


class DeliveryZoneListSerializer(serializers.ModelSerializer):
    """Simple list serializer without geometry for performance."""

    class Meta:
        model = DeliveryZone
        fields = [
            "id",
            "name",
            "delivery_fee",
            "minimum_order",
            "estimated_time_minutes",
            "is_active",
        ]


class CheckAddressSerializer(serializers.Serializer):
    """Serializer for address check request."""

    lat = serializers.FloatField(min_value=-90, max_value=90)
    lng = serializers.FloatField(min_value=-180, max_value=180)


class CheckAddressResponseSerializer(serializers.Serializer):
    """Serializer for address check response."""

    deliverable = serializers.BooleanField()
    zone = DeliveryZoneListSerializer(required=False, allow_null=True)
    message = serializers.CharField(required=False)


class DriverSerializer(serializers.ModelSerializer):
    """Serializer for Driver model."""

    user_name = serializers.CharField(source="user.name", read_only=True)
    user_phone = serializers.CharField(source="user.phone", read_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = [
            "id",
            "user",
            "user_name",
            "user_phone",
            "phone",
            "vehicle_type",
            "vehicle_plate",
            "is_available",
            "went_online_at",
            "latitude",
            "longitude",
            "location_updated_at",
            "total_deliveries",
            "average_rating",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "is_available",
            "went_online_at",
            "location_updated_at",
            "total_deliveries",
            "average_rating",
        ]

    def get_latitude(self, obj):
        if obj.current_location:
            return obj.current_location.y  # GIS Point: x=lng, y=lat
        return None

    def get_longitude(self, obj):
        if obj.current_location:
            return obj.current_location.x
        return None


class DriverCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a driver profile."""

    class Meta:
        model = Driver
        fields = ["user", "phone", "vehicle_type", "vehicle_plate"]

    def validate_user(self, value):
        """Ensure user has driver role and belongs to same restaurant."""
        if value.role != "driver":
            raise serializers.ValidationError("User must have 'driver' role")

        request = self.context.get("request")
        if request and hasattr(request, "restaurant"):
            if value.restaurant_id != request.restaurant.id:
                raise serializers.ValidationError(
                    "User must belong to same restaurant"
                )

        return value


class DriverLocationUpdateSerializer(serializers.Serializer):
    """Serializer for driver location update."""

    lat = serializers.FloatField(min_value=-90, max_value=90)
    lng = serializers.FloatField(min_value=-180, max_value=180)
