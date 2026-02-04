"""Views for delivery API."""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.views import TenantModelViewSet

from .models import Delivery, DeliveryStatus, DeliveryZone, Driver
from .serializers import (
    CheckAddressSerializer,
    DeliveryConfirmSerializer,
    DeliveryCreateSerializer,
    DeliverySerializer,
    DeliveryStatusUpdateSerializer,
    DeliveryZoneListSerializer,
    DeliveryZoneSerializer,
    DriverCreateSerializer,
    DriverLocationUpdateSerializer,
    DriverSerializer,
)
from .services import assign_driver_to_delivery, create_delivery_for_order


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


class DeliveryViewSet(TenantModelViewSet):
    """
    ViewSet for delivery management.

    list: Return all deliveries
    retrieve: Return single delivery
    create: Create delivery for an order
    active: Return driver's active deliveries
    update_status: Transition delivery status
    confirm: Confirm delivery with proof
    assign: Manually trigger driver assignment
    """

    serializer_class = DeliverySerializer

    def get_queryset(self):
        return Delivery.objects.filter(
            restaurant=self.request.restaurant
        ).select_related("order", "driver__user", "zone")

    def get_serializer_class(self):
        if self.action == "create":
            return DeliveryCreateSerializer
        if self.action == "update_status":
            return DeliveryStatusUpdateSerializer
        if self.action == "confirm":
            return DeliveryConfirmSerializer
        return DeliverySerializer

    def create(self, request):
        """Create a delivery for an order."""
        serializer = DeliveryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.orders.models import Order

        try:
            order = Order.objects.get(
                id=serializer.validated_data["order_id"],
                restaurant=request.restaurant,
            )
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            delivery = create_delivery_for_order(
                order=order,
                delivery_address=serializer.validated_data["delivery_address"],
                delivery_lat=serializer.validated_data["delivery_lat"],
                delivery_lng=serializer.validated_data["delivery_lng"],
                delivery_notes=serializer.validated_data.get("delivery_notes", ""),
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            DeliverySerializer(delivery).data, status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["get"])
    def active(self, request):
        """
        Get active deliveries for current driver.

        GET /api/v1/delivery/deliveries/active/
        """
        try:
            driver = Driver.objects.get(
                restaurant=request.restaurant, user=request.user
            )
        except Driver.DoesNotExist:
            return Response(
                {"error": "No driver profile found"}, status=status.HTTP_404_NOT_FOUND
            )

        deliveries = Delivery.objects.filter(
            restaurant=request.restaurant,
            driver=driver,
            status__in=[
                DeliveryStatus.ASSIGNED,
                DeliveryStatus.PICKED_UP,
                DeliveryStatus.EN_ROUTE,
            ],
        ).select_related("order", "zone")

        return Response(DeliverySerializer(deliveries, many=True).data)

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        """
        Update delivery status.

        POST /api/v1/delivery/deliveries/{id}/update_status/
        Body: {"status": "picked_up"}
        """
        delivery = self.get_object()
        serializer = DeliveryStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]

        try:
            if new_status == "picked_up":
                delivery.mark_picked_up()
            elif new_status == "en_route":
                delivery.mark_en_route()
            elif new_status == "delivered":
                delivery.mark_delivered(
                    proof_type=serializer.validated_data.get("proof_type", "none"),
                    proof_data=serializer.validated_data.get("proof_data", ""),
                    recipient_name=serializer.validated_data.get("recipient_name", ""),
                )
            elif new_status == "cancelled":
                delivery.cancel(
                    reason=serializer.validated_data.get("cancel_reason", "")
                )

            delivery.save()

            # Broadcast status update via WebSocket
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            from django.utils import timezone

            if delivery.driver_id:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"driver_location_{delivery.driver_id}",
                    {
                        "type": "delivery_status_update",
                        "status": delivery.status,
                        "timestamp": timezone.now().isoformat(),
                    },
                )

            return Response(DeliverySerializer(delivery).data)

        except Exception as e:
            return Response(
                {"error": f"Invalid status transition: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """
        Confirm delivery with proof (photo or signature).

        POST /api/v1/delivery/deliveries/{id}/confirm/
        Body: {"proof_type": "signature", "proof_data": "base64...", "recipient_name": "John"}
        """
        delivery = self.get_object()
        serializer = DeliveryConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if delivery.status != DeliveryStatus.EN_ROUTE:
            return Response(
                {"error": "Delivery must be en_route to confirm"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            delivery.mark_delivered(
                proof_type=serializer.validated_data["proof_type"],
                proof_data=serializer.validated_data.get("proof_data", ""),
                recipient_name=serializer.validated_data.get("recipient_name", ""),
            )

            # Handle photo upload if provided
            if "proof_photo" in request.FILES:
                delivery.proof_photo = request.FILES["proof_photo"]

            delivery.save()

            # Update driver stats and make available
            if delivery.driver:
                delivery.driver.total_deliveries += 1
                delivery.driver.is_available = True
                delivery.driver.save(update_fields=["total_deliveries", "is_available"])

            return Response(DeliverySerializer(delivery).data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """
        Manually trigger driver assignment.

        POST /api/v1/delivery/deliveries/{id}/assign/

        This endpoint allows managers to manually trigger auto-assignment
        or can be extended to accept a specific driver_id for manual override.
        """
        delivery = self.get_object()

        if delivery.status != DeliveryStatus.PENDING_ASSIGNMENT:
            return Response(
                {"error": "Delivery already assigned or not pending"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = assign_driver_to_delivery(delivery.id)

        if result is None:
            return Response(
                {"error": "No available drivers found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(DeliverySerializer(result).data)


class DeliveryTrackingView(APIView):
    """
    Public endpoint for customer delivery tracking.

    GET /api/v1/delivery/track/{delivery_id}/

    No authentication required - delivery ID serves as access key.
    """

    permission_classes = [AllowAny]

    def get(self, request, delivery_id):
        try:
            delivery = Delivery.all_objects.select_related(
                "driver__user", "zone", "order__restaurant"
            ).get(id=delivery_id)
        except Delivery.DoesNotExist:
            return Response(
                {"error": "Delivery not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Build response with necessary tracking info
        data = {
            "id": str(delivery.id),
            "status": delivery.status,
            "delivery_address": delivery.delivery_address,
            "delivery_lat": (
                delivery.delivery_location.y if delivery.delivery_location else None
            ),
            "delivery_lng": (
                delivery.delivery_location.x if delivery.delivery_location else None
            ),
            "estimated_delivery_time": (
                delivery.estimated_delivery_time.isoformat()
                if delivery.estimated_delivery_time
                else None
            ),
            "customer_name": delivery.customer_name,
            "customer_phone": delivery.customer_phone,
            "delivery_fee": delivery.delivery_fee,
            "order_number": delivery.order.order_number,
            "created_at": delivery.created_at.isoformat(),
            "assigned_at": (
                delivery.assigned_at.isoformat() if delivery.assigned_at else None
            ),
            "picked_up_at": (
                delivery.picked_up_at.isoformat() if delivery.picked_up_at else None
            ),
            "en_route_at": (
                delivery.en_route_at.isoformat() if delivery.en_route_at else None
            ),
            "delivered_at": (
                delivery.delivered_at.isoformat() if delivery.delivered_at else None
            ),
        }

        # Add driver info if assigned
        if delivery.driver:
            data["driver"] = {
                "name": delivery.driver.user.name,
                "phone": delivery.driver.phone,
                "vehicle_type": delivery.driver.vehicle_type,
            }
            if delivery.driver.current_location:
                data["driver"]["lat"] = delivery.driver.current_location.y
                data["driver"]["lng"] = delivery.driver.current_location.x

        # Add restaurant info
        restaurant = delivery.order.restaurant
        data["restaurant"] = {
            "name": restaurant.name,
            "phone": restaurant.phone,
            "address": restaurant.address,
        }
        if restaurant.latitude and restaurant.longitude:
            data["restaurant"]["lat"] = float(restaurant.latitude)
            data["restaurant"]["lng"] = float(restaurant.longitude)

        return Response(data)
