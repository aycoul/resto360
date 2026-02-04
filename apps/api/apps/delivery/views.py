"""Views for delivery API."""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.views import TenantModelViewSet

from .models import DeliveryZone, Driver
from .serializers import (
    CheckAddressSerializer,
    DeliveryZoneListSerializer,
    DeliveryZoneSerializer,
    DriverCreateSerializer,
    DriverLocationUpdateSerializer,
    DriverSerializer,
)


class DeliveryZoneViewSet(TenantModelViewSet):
    """
    ViewSet for delivery zone management.

    list: Return all zones (simple list without geometry)
    retrieve: Return single zone with full GeoJSON geometry
    create/update/delete: Manage zones
    check_address: Check if coordinates are within any delivery zone
    """

    serializer_class = DeliveryZoneSerializer

    def get_queryset(self):
        return DeliveryZone.objects.filter(restaurant=self.request.restaurant)

    def get_serializer_class(self):
        if self.action == "list":
            return DeliveryZoneListSerializer
        return DeliveryZoneSerializer

    def perform_create(self, serializer):
        """Associate zone with current restaurant."""
        serializer.save(restaurant=self.request.restaurant)

    @action(detail=False, methods=["post"])
    def check_address(self, request):
        """
        Check if an address (lat/lng) is within any delivery zone.

        POST /api/v1/delivery/zones/check_address/
        Body: {"lat": 5.3364, "lng": -3.9667}

        Returns:
        - deliverable: true/false
        - zone: zone details if deliverable
        - message: explanation if not deliverable
        """
        serializer = CheckAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lat = serializer.validated_data["lat"]
        lng = serializer.validated_data["lng"]

        zone = DeliveryZone.find_zone_for_location(
            restaurant=request.restaurant, lat=lat, lng=lng
        )

        if zone:
            response_data = {
                "deliverable": True,
                "zone": DeliveryZoneListSerializer(zone).data,
            }
        else:
            response_data = {
                "deliverable": False,
                "zone": None,
                "message": "Address is outside delivery area",
            }

        return Response(response_data)


class DriverViewSet(TenantModelViewSet):
    """
    ViewSet for driver management.

    list: Return all drivers for restaurant
    retrieve: Return single driver
    create: Create driver profile (links to existing user with driver role)
    toggle_availability: Go online/offline
    update_location: Update driver's current GPS position
    """

    serializer_class = DriverSerializer

    def get_queryset(self):
        return Driver.objects.filter(restaurant=self.request.restaurant)

    def get_serializer_class(self):
        if self.action == "create":
            return DriverCreateSerializer
        return DriverSerializer

    def perform_create(self, serializer):
        """Associate driver with current restaurant."""
        serializer.save(restaurant=self.request.restaurant)

    @action(detail=True, methods=["post"])
    def toggle_availability(self, request, pk=None):
        """
        Toggle driver online/offline status.

        POST /api/v1/delivery/drivers/{id}/toggle_availability/
        """
        driver = self.get_object()

        if driver.is_available:
            driver.go_offline()
        else:
            driver.go_online()

        return Response(DriverSerializer(driver).data)

    @action(detail=True, methods=["post"])
    def update_location(self, request, pk=None):
        """
        Update driver's current location.

        POST /api/v1/delivery/drivers/{id}/update_location/
        Body: {"lat": 5.3364, "lng": -3.9667}
        """
        driver = self.get_object()

        serializer = DriverLocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        driver.update_location(
            lat=serializer.validated_data["lat"], lng=serializer.validated_data["lng"]
        )

        return Response(DriverSerializer(driver).data)

    @action(detail=False, methods=["get"])
    def me(self, request):
        """
        Get current user's driver profile.

        GET /api/v1/delivery/drivers/me/
        """
        try:
            driver = Driver.objects.get(
                restaurant=request.restaurant, user=request.user
            )
            return Response(DriverSerializer(driver).data)
        except Driver.DoesNotExist:
            return Response(
                {"error": "No driver profile found"}, status=status.HTTP_404_NOT_FOUND
            )
