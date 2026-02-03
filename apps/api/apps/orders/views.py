"""Order views for RESTO360."""

from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.context import set_current_restaurant
from apps.core.permissions import IsCashier, IsOwnerOrManager
from apps.core.views import TenantModelViewSet

from .models import Order, OrderItem, OrderItemModifier, OrderStatus, Table
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
    TableSerializer,
)


class TableViewSet(TenantModelViewSet):
    """ViewSet for restaurant tables."""

    serializer_class = TableSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrManager()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Get tables filtered by tenant."""
        qs = Table.objects.all()

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")

        return qs


class OrderViewSet(TenantModelViewSet):
    """ViewSet for orders."""

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            return [IsAuthenticated(), IsCashier()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Get orders filtered by tenant with optimized loading."""
        qs = Order.objects.all()

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Filter by order type
        order_type = self.request.query_params.get("order_type")
        if order_type:
            qs = qs.filter(order_type=order_type)

        # Filter by date range
        date_from = self.request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        # Prefetch items and modifiers for detail views
        if self.action == "retrieve":
            qs = qs.prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.all_objects.prefetch_related(
                        Prefetch(
                            "modifiers",
                            queryset=OrderItemModifier.all_objects.all(),
                        )
                    ),
                )
            )
        else:
            # For list views, just include items count
            qs = qs.prefetch_related("items")

        return qs.select_related("table", "cashier")

    def create(self, request, *args, **kwargs):
        """Create a new order."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # Return the full order with items
        output_serializer = OrderSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        """Update order status with validation."""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(
            data=request.data,
            context={"order": order, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        updated_order = serializer.update(order, serializer.validated_data)

        output_serializer = OrderSerializer(updated_order)
        return Response(output_serializer.data)


class KitchenQueueView(APIView):
    """View for kitchen display system."""

    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        """Set tenant context after authentication."""
        super().initial(request, *args, **kwargs)
        if request.user.is_authenticated:
            if hasattr(request.user, "restaurant") and request.user.restaurant:
                set_current_restaurant(request.user.restaurant)

    def finalize_response(self, request, response, *args, **kwargs):
        """Clear tenant context after response."""
        response = super().finalize_response(request, response, *args, **kwargs)
        set_current_restaurant(None)
        return response

    def get(self, request):
        """
        Get orders for kitchen display.

        Returns pending and preparing orders, oldest first.
        """
        orders = (
            Order.objects.filter(
                status__in=[OrderStatus.PENDING, OrderStatus.PREPARING]
            )
            .order_by("created_at")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.all_objects.prefetch_related(
                        Prefetch(
                            "modifiers",
                            queryset=OrderItemModifier.all_objects.all(),
                        )
                    ),
                )
            )
            .select_related("table")
        )

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
