from django.db import models as db_models
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.context import get_current_restaurant
from apps.core.permissions import IsOwnerOrManager
from apps.core.views import TenantContextMixin, TenantModelViewSet

from .models import MenuItemIngredient, StockItem, StockMovement
from .serializers import (
    AddStockSerializer,
    AdjustStockSerializer,
    CurrentStockReportSerializer,
    MenuItemIngredientSerializer,
    MovementReportRequestSerializer,
    StockItemListSerializer,
    StockItemSerializer,
    StockMovementSerializer,
)
from .services import (
    InsufficientStockError,
    add_stock,
    adjust_stock,
    get_current_stock_report,
    get_movement_report,
)


class StockItemViewSet(TenantModelViewSet):
    """
    ViewSet for managing stock items.

    Provides CRUD operations plus custom actions for stock operations.
    Stock quantities are updated only via add_stock and adjust actions.
    """

    def get_serializer_class(self):
        if self.action == "list":
            return StockItemListSerializer
        return StockItemSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrManager()]
        if self.action in ("add_stock", "adjust"):
            return [IsAuthenticated(), IsOwnerOrManager()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Get stock items filtered by tenant."""
        qs = StockItem.objects.all()

        # Filter by active status if requested
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")

        # Filter by low stock
        low_stock_only = self.request.query_params.get("low_stock")
        if low_stock_only and low_stock_only.lower() == "true":
            qs = qs.filter(
                low_stock_threshold__isnull=False,
                current_quantity__lte=db_models.F("low_stock_threshold"),
            )

        return qs

    @action(detail=True, methods=["post"], url_path="add-stock")
    def add_stock(self, request, pk=None):
        """
        Add stock to an item.

        POST /api/v1/inventory/stock-items/{id}/add-stock/
        {
            "quantity": 10.5,
            "reason": "purchase",
            "notes": "Order #123"
        }
        """
        serializer = AddStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        stock_item = self.get_object()

        try:
            updated_item = add_stock(
                stock_item_id=stock_item.id,
                quantity=serializer.validated_data["quantity"],
                reason=serializer.validated_data["reason"],
                user=request.user,
                notes=serializer.validated_data.get("notes", ""),
            )
            return Response(
                StockItemSerializer(updated_item).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def adjust(self, request, pk=None):
        """
        Adjust stock to a specific quantity.

        POST /api/v1/inventory/stock-items/{id}/adjust/
        {
            "new_quantity": 25.0,
            "reason": "correction",
            "notes": "Physical count showed 25 units"
        }
        """
        serializer = AdjustStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        stock_item = self.get_object()

        try:
            updated_item = adjust_stock(
                stock_item_id=stock_item.id,
                new_quantity=serializer.validated_data["new_quantity"],
                reason=serializer.validated_data["reason"],
                user=request.user,
                notes=serializer.validated_data.get("notes", ""),
            )
            return Response(
                StockItemSerializer(updated_item).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"])
    def movements(self, request, pk=None):
        """
        Get movement history for a specific stock item.

        GET /api/v1/inventory/stock-items/{id}/movements/
        """
        stock_item = self.get_object()
        movements = StockMovement.all_objects.filter(
            stock_item=stock_item
        ).order_by("-created_at")

        # Apply pagination
        page = self.paginate_queryset(movements)
        if page is not None:
            serializer = StockMovementSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = StockMovementSerializer(movements, many=True)
        return Response(serializer.data)


class TenantReadOnlyModelViewSet(TenantModelViewSet):
    """Base ReadOnlyModelViewSet with tenant context support."""

    http_method_names = ["get", "head", "options"]


class StockMovementViewSet(TenantReadOnlyModelViewSet):
    """
    ViewSet for viewing stock movements (read-only).

    Movements are created via stock item actions, not directly.
    This endpoint is for viewing and filtering movement history.
    """

    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get movements filtered by tenant and optional stock_item."""
        qs = StockMovement.objects.all()

        # Filter by stock item if provided
        stock_item_id = self.request.query_params.get("stock_item")
        if stock_item_id:
            qs = qs.filter(stock_item_id=stock_item_id)

        # Filter by movement type
        movement_type = self.request.query_params.get("movement_type")
        if movement_type:
            qs = qs.filter(movement_type=movement_type)

        # Filter by reason
        reason = self.request.query_params.get("reason")
        if reason:
            qs = qs.filter(reason=reason)

        return qs.order_by("-created_at")


class MenuItemIngredientViewSet(TenantModelViewSet):
    """
    ViewSet for managing recipe ingredient mappings.

    GET /api/inventory/recipes/ - List all mappings
    POST /api/inventory/recipes/ - Create mapping
    GET /api/inventory/recipes/{id}/ - Get mapping detail
    PUT/PATCH /api/inventory/recipes/{id}/ - Update mapping
    DELETE /api/inventory/recipes/{id}/ - Delete mapping
    GET /api/inventory/recipes/?menu_item={id} - Filter by menu item
    GET /api/inventory/recipes/?stock_item={id} - Filter by stock item
    """

    serializer_class = MenuItemIngredientSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        """Get recipe mappings filtered by tenant and optional filters."""
        qs = MenuItemIngredient.objects.all()

        # Filter by menu_item if provided
        menu_item_id = self.request.query_params.get("menu_item")
        if menu_item_id:
            qs = qs.filter(menu_item_id=menu_item_id)

        # Filter by stock_item if provided
        stock_item_id = self.request.query_params.get("stock_item")
        if stock_item_id:
            qs = qs.filter(stock_item_id=stock_item_id)

        return qs.select_related("menu_item", "stock_item")


class ReportViewSet(TenantContextMixin, viewsets.ViewSet):
    """
    ViewSet for inventory reports.

    GET /api/inventory/reports/current-stock/ - Current stock levels
    GET /api/inventory/reports/low-stock/ - Items below threshold
    GET /api/inventory/reports/movements/?start_date=&end_date= - Movement history
    """

    permission_classes = [IsAuthenticated, IsOwnerOrManager]

    @action(detail=False, methods=["get"], url_path="current-stock")
    def current_stock(self, request):
        """Get current stock levels for all items."""
        restaurant = get_current_restaurant()
        include_inactive = (
            request.query_params.get("include_inactive", "false").lower() == "true"
        )

        items = get_current_stock_report(restaurant, include_inactive=include_inactive)

        serializer = CurrentStockReportSerializer(items, many=True)
        return Response(
            {
                "count": items.count(),
                "items": serializer.data,
            }
        )

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        """Get items at or below low stock threshold."""
        restaurant = get_current_restaurant()
        items = get_current_stock_report(restaurant, low_stock_only=True)

        serializer = CurrentStockReportSerializer(items, many=True)
        return Response(
            {
                "count": items.count(),
                "items": serializer.data,
            }
        )

    @action(detail=False, methods=["get"], url_path="movements")
    def movements(self, request):
        """
        Get movement report for date range.

        Query params:
        - start_date: YYYY-MM-DD (required)
        - end_date: YYYY-MM-DD (required)
        - stock_item: UUID (optional, filter to specific item)
        """
        # Validate request params
        request_serializer = MovementReportRequestSerializer(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)

        restaurant = get_current_restaurant()
        report = get_movement_report(
            restaurant=restaurant,
            start_date=request_serializer.validated_data["start_date"],
            end_date=request_serializer.validated_data["end_date"],
            stock_item_id=request_serializer.validated_data.get("stock_item"),
        )

        return Response(report)
