"""Reorder views for BIZ360."""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.context import set_current_business
from apps.orders.models import Order, OrderItem, OrderItemModifier
from apps.orders.services import get_next_order_number

from .models import CustomerProfile, OrderHistory, ReorderQRCode, ReorderScan
from .serializers import (
    CustomerLookupSerializer,
    CustomerProfileSerializer,
    OrderHistoryListSerializer,
    OrderHistorySerializer,
    PublicReorderInfoSerializer,
    ReorderFromHistorySerializer,
    ReorderQRCodeSerializer,
    ReorderScanSerializer,
    ReorderSubmitSerializer,
)


class ReorderQRCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reorder QR codes."""

    permission_classes = [IsAuthenticated]
    serializer_class = ReorderQRCodeSerializer

    def get_queryset(self):
        set_current_business(self.request.user.business)
        return ReorderQRCode.objects.filter(
            business=self.request.user.business
        ).select_related("product")

    @action(detail=True, methods=["get"])
    def analytics(self, request, pk=None):
        """Get analytics for a QR code."""
        qr_code = self.get_object()
        scans = ReorderScan.objects.filter(qr_code=qr_code)

        # Daily stats for last 30 days
        from datetime import timedelta
        from django.db.models import Count
        from django.db.models.functions import TruncDate

        today = timezone.localdate()
        start_date = today - timedelta(days=30)

        daily_stats = scans.filter(
            scanned_at__date__gte=start_date
        ).annotate(
            date=TruncDate("scanned_at")
        ).values("date").annotate(
            scans=Count("id"),
            conversions=Count("id", filter=models.Q(converted_to_order=True)),
        ).order_by("date")

        return Response({
            "total_scans": qr_code.scan_count,
            "total_orders": qr_code.order_count,
            "conversion_rate": (
                round(qr_code.order_count / qr_code.scan_count * 100, 1)
                if qr_code.scan_count > 0 else 0
            ),
            "daily_stats": list(daily_stats),
        })


class ReorderScanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing QR scan records."""

    permission_classes = [IsAuthenticated]
    serializer_class = ReorderScanSerializer

    def get_queryset(self):
        set_current_business(self.request.user.business)
        return ReorderScan.objects.filter(
            business=self.request.user.business
        ).select_related("qr_code__product", "order")


class PublicReorderView(viewsets.ViewSet):
    """
    Public views for QR reorder (no authentication required).

    Handles the customer-facing reorder flow:
    1. GET /reorder/{code}/ - Get product info for reorder page
    2. POST /reorder/{code}/submit/ - Submit the reorder
    """

    permission_classes = [AllowAny]

    def retrieve(self, request, code=None):
        """Get reorder page information by QR code."""
        try:
            qr_code = ReorderQRCode.all_objects.get(code=code, is_active=True)
        except ReorderQRCode.DoesNotExist:
            return Response(
                {"error": "Invalid or inactive QR code"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Track scan
        ReorderScan.objects.create(
            business=qr_code.business,
            qr_code=qr_code,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            referrer=request.META.get("HTTP_REFERER", ""),
        )
        qr_code.increment_scan()

        # Build response
        product = qr_code.product
        business = qr_code.business

        data = {
            "product_name": product.name,
            "product_description": product.description,
            "product_price": product.price,
            "product_image": product.image.url if product.image else None,
            "business_name": business.name,
            "business_logo": business.logo.url if business.logo else None,
            "default_quantity": qr_code.default_quantity,
            "min_quantity": qr_code.min_quantity,
            "max_quantity": qr_code.max_quantity,
            "require_name": qr_code.require_name,
            "require_phone": qr_code.require_phone,
            "require_address": qr_code.require_address,
            "promo_message": qr_code.promo_message,
            "discount_percent": qr_code.discount_percent,
        }

        return Response(PublicReorderInfoSerializer(data).data)

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, code=None):
        """Submit a reorder from QR scan."""
        try:
            qr_code = ReorderQRCode.all_objects.get(code=code, is_active=True)
        except ReorderQRCode.DoesNotExist:
            return Response(
                {"error": "Invalid or inactive QR code"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ReorderSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Validate required fields
        if qr_code.require_name and not data.get("customer_name"):
            return Response(
                {"error": "Customer name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if qr_code.require_address and not data.get("customer_address"):
            return Response(
                {"error": "Delivery address is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate quantity
        quantity = data["quantity"]
        if quantity < qr_code.min_quantity or quantity > qr_code.max_quantity:
            return Response(
                {"error": f"Quantity must be between {qr_code.min_quantity} and {qr_code.max_quantity}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create order
        with transaction.atomic():
            business = qr_code.business
            product = qr_code.product

            # Calculate price with discount
            unit_price = product.price
            if qr_code.discount_percent > 0:
                discount = unit_price * qr_code.discount_percent / 100
                unit_price = int(unit_price - discount)

            line_total = unit_price * quantity

            # Create order
            order = Order.objects.create(
                business=business,
                order_number=get_next_order_number(business),
                order_type="online",
                customer_name=data.get("customer_name", ""),
                customer_phone=data["customer_phone"],
                customer_email=data.get("customer_email", ""),
                customer_address=data.get("customer_address", ""),
                notes=data.get("notes", f"QR Reorder: {product.name}"),
                subtotal=line_total,
                total=line_total,
                tax_rate=business.default_tax_rate,
            )
            order.calculate_totals()
            order.save()

            # Create order item
            OrderItem.objects.create(
                business=business,
                order=order,
                menu_item=product,
                name=product.name,
                unit_price=unit_price,
                quantity=quantity,
                line_total=line_total,
            )

            # Track conversion
            scan = ReorderScan.objects.filter(
                qr_code=qr_code,
                ip_address=self._get_client_ip(request),
                converted_to_order=False,
            ).order_by("-scanned_at").first()

            if scan:
                scan.converted_to_order = True
                scan.order = order
                scan.converted_at = timezone.now()
                scan.save()

            qr_code.increment_order()

            # Link to customer profile
            self._link_customer_order(data["customer_phone"], order, business)

        return Response({
            "success": True,
            "order_id": str(order.id),
            "order_number": order.order_number,
            "total": order.total,
        })

    def _get_client_ip(self, request):
        """Extract client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def _link_customer_order(self, phone, order, business):
        """Link order to customer profile."""
        customer, _ = CustomerProfile.objects.get_or_create(
            phone=phone,
            defaults={
                "name": order.customer_name,
                "email": order.customer_email,
                "default_address": order.customer_address,
            }
        )

        OrderHistory.objects.create(
            business=business,
            customer=customer,
            order=order,
            order_total=order.total,
            order_date=order.created_at,
            item_count=order.items.count(),
        )

        customer.update_stats(order)


class CustomerOrderHistoryViewSet(viewsets.ViewSet):
    """
    Customer order history views (public, requires phone verification).

    Allows customers to:
    1. Look up their order history by phone
    2. Reorder from previous orders
    """

    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def lookup(self, request):
        """Look up customer by phone number."""
        serializer = CustomerLookupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]

        try:
            customer = CustomerProfile.objects.get(phone=phone)
        except CustomerProfile.DoesNotExist:
            return Response(
                {"error": "No order history found for this phone number"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get order history
        history = OrderHistory.objects.filter(
            customer=customer
        ).select_related("business", "order").order_by("-order_date")[:20]

        return Response({
            "customer": CustomerProfileSerializer(customer).data,
            "orders": OrderHistoryListSerializer(history, many=True).data,
        })

    @action(detail=False, methods=["get"])
    def order_detail(self, request):
        """Get detailed order for potential reorder."""
        history_id = request.query_params.get("id")
        phone = request.query_params.get("phone")

        if not history_id or not phone:
            return Response(
                {"error": "Order ID and phone are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            history = OrderHistory.objects.get(
                id=history_id,
                customer__phone=phone,
            )
        except OrderHistory.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(OrderHistorySerializer(history).data)

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        """Reorder from order history."""
        serializer = ReorderFromHistorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            history = OrderHistory.objects.get(
                id=data["order_history_id"],
                customer__phone=data["customer_phone"],
            )
        except OrderHistory.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        original_order = history.order
        business = history.business

        with transaction.atomic():
            # Create new order
            new_order = Order.objects.create(
                business=business,
                order_number=get_next_order_number(business),
                order_type=original_order.order_type,
                customer_name=history.customer.name,
                customer_phone=history.customer.phone,
                customer_address=data.get("customer_address", history.customer.default_address),
                notes=f"Reorder from Order #{original_order.order_number}",
                tax_rate=business.default_tax_rate,
            )

            # Copy items with optional quantity adjustments
            item_quantities = data.get("item_quantities", {})
            subtotal = 0

            for orig_item in original_order.items.all():
                # Get adjusted quantity or use original
                new_qty = item_quantities.get(str(orig_item.id), orig_item.quantity)
                if new_qty <= 0:
                    continue  # Skip if quantity is 0

                # Get current product price
                if orig_item.menu_item and orig_item.menu_item.is_available:
                    unit_price = orig_item.menu_item.price
                else:
                    # Use historical price if product unavailable
                    unit_price = orig_item.unit_price

                line_total = unit_price * new_qty

                new_item = OrderItem.objects.create(
                    business=business,
                    order=new_order,
                    menu_item=orig_item.menu_item,
                    name=orig_item.name,
                    unit_price=unit_price,
                    quantity=new_qty,
                    line_total=line_total,
                )

                # Copy modifiers
                for orig_mod in orig_item.modifiers.all():
                    OrderItemModifier.objects.create(
                        business=business,
                        order_item=new_item,
                        modifier_option=orig_mod.modifier_option,
                        name=orig_mod.name,
                        price_adjustment=orig_mod.price_adjustment,
                    )

                subtotal += line_total

            new_order.subtotal = subtotal
            new_order.calculate_totals()
            new_order.save()

            # Track reorder
            history.increment_reorder()

            # Create new history entry
            OrderHistory.objects.create(
                business=business,
                customer=history.customer,
                order=new_order,
                order_total=new_order.total,
                order_date=new_order.created_at,
                item_count=new_order.items.count(),
            )

            history.customer.update_stats(new_order)

        return Response({
            "success": True,
            "order_id": str(new_order.id),
            "order_number": new_order.order_number,
            "total": new_order.total,
        })
