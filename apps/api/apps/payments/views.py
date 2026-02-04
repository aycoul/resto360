"""ViewSets for payment API endpoints."""

import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsOwnerOrManager
from apps.core.views import TenantContextMixin
from apps.orders.models import Order

from .models import CashDrawerSession, Payment, PaymentMethod
from .serializers import (
    CashDrawerSessionSerializer,
    CloseDrawerSerializer,
    InitiatePaymentSerializer,
    OpenDrawerSerializer,
    PaymentMethodSerializer,
    PaymentSerializer,
    RefundRequestSerializer,
)
from .services import (
    get_daily_reconciliation,
    get_payment_status,
    get_reconciliation_range,
    initiate_payment,
    process_refund_request,
)
from .tasks import process_webhook_event

logger = logging.getLogger(__name__)


class PaymentMethodViewSet(TenantContextMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing payment methods.

    GET /api/payments/methods/ - List active payment methods
    POST /api/payments/methods/ - Create payment method
    GET /api/payments/methods/{id}/ - Get payment method detail
    PUT/PATCH /api/payments/methods/{id}/ - Update payment method
    DELETE /api/payments/methods/{id}/ - Delete payment method
    """

    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get payment methods filtered by tenant."""
        return PaymentMethod.objects.all().order_by("display_order", "name")


class PaymentViewSet(TenantContextMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing payments.

    GET /api/payments/ - List payments for the restaurant
    GET /api/payments/{id}/ - Get payment detail
    POST /api/payments/initiate/ - Initiate a new payment
    GET /api/payments/{id}/status/ - Get payment status
    """

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        """Get payments filtered by tenant."""
        queryset = Payment.objects.all().order_by("-initiated_at")

        # Filter by status if provided
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by order if provided
        order_id = self.request.query_params.get("order_id")
        if order_id:
            queryset = queryset.filter(order_id=order_id)

        return queryset

    @action(detail=False, methods=["post"])
    def initiate(self, request):
        """
        Initiate a new payment.

        POST /api/payments/initiate/
        {
            "order_id": "uuid",
            "provider_code": "wave",
            "idempotency_key": "unique-key",
            "callback_url": "https://...",  # optional
            "success_url": "https://...",   # optional
            "error_url": "https://..."      # optional
        }

        Returns payment object with redirect_url for mobile money providers.
        """
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        order_id = data["order_id"]
        provider_code = data["provider_code"]
        idempotency_key = data["idempotency_key"]

        # Get the order
        try:
            order = Order.objects.filter(
                restaurant=request.user.restaurant,
                id=order_id,
            ).first()

            if not order:
                return Response(
                    {"detail": "Order not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Exception as e:
            logger.error("Error looking up order %s: %s", order_id, str(e))
            return Response(
                {"detail": "Invalid order ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the payment method
        payment_method = PaymentMethod.objects.filter(
            restaurant=request.user.restaurant,
            provider_code=provider_code,
            is_active=True,
        ).first()

        if not payment_method:
            return Response(
                {"detail": f"Payment method '{provider_code}' not found or inactive."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Initiate the payment
        result = initiate_payment(
            order=order,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            request=request,
            callback_url=data.get("callback_url", ""),
            success_url=data.get("success_url", ""),
            error_url=data.get("error_url", ""),
        )

        # Serialize the response
        response_data = {
            "payment": PaymentSerializer(result["payment"]).data,
            "redirect_url": result["redirect_url"],
            "status": result["status"],
            "is_duplicate": result["is_duplicate"],
        }

        # Return 200 for duplicate, 201 for new payment
        http_status = status.HTTP_200_OK if result["is_duplicate"] else status.HTTP_201_CREATED
        return Response(response_data, status=http_status)

    @action(detail=True, methods=["get"], url_path="status")
    def get_status(self, request, pk=None):
        """
        Get the current status of a payment.

        GET /api/payments/{id}/status/

        Returns payment status information.
        """
        result = get_payment_status(
            payment_id=pk,
            restaurant=request.user.restaurant,
        )

        if not result:
            return Response(
                {"detail": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(result)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        """
        Initiate a refund for a payment.

        POST /api/payments/{id}/refund/
        {
            "amount": 5000,       # Optional - null or omit for full refund
            "reason": "Customer request"  # Optional
        }

        Returns refund result.
        """
        # Get the payment
        payment = self.get_queryset().filter(id=pk).first()

        if not payment:
            return Response(
                {"detail": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate request data
        serializer = RefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        refund_amount = data.get("amount")
        reason = data.get("reason", "")

        # Process the refund
        result = process_refund_request(
            payment=payment,
            amount=refund_amount,
            reason=reason,
        )

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class BaseWebhookView(View):
    """
    Base class for webhook views.

    Webhooks have NO authentication - providers can't authenticate.
    Processing is queued asynchronously for quick HTTP response.
    """

    provider_code = None  # Subclasses must set this

    def post(self, request):
        """
        Handle webhook POST request.

        Returns 200 immediately and queues processing.
        """
        if not self.provider_code:
            return JsonResponse(
                {"error": "Provider code not configured"},
                status=500,
            )

        # Extract headers as dict
        headers = {}
        for key, value in request.headers.items():
            headers[key] = value

        # Get raw body as string
        body = request.body.decode("utf-8")

        # Log receipt
        logger.info(
            "Received %s webhook, body length: %d",
            self.provider_code,
            len(body),
        )

        # Queue for async processing
        try:
            process_webhook_event.delay(
                provider_code=self.provider_code,
                headers=headers,
                body=body,
            )
        except Exception as e:
            logger.error(
                "Failed to queue %s webhook: %s",
                self.provider_code,
                str(e),
            )
            # Still return 200 - we received it

        # Return 200 quickly
        return JsonResponse({"received": True})


class WaveWebhookView(BaseWebhookView):
    """Handle Wave payment webhooks."""

    provider_code = "wave"


class OrangeWebhookView(BaseWebhookView):
    """Handle Orange Money webhooks."""

    provider_code = "orange"


class MTNWebhookView(BaseWebhookView):
    """Handle MTN MoMo webhooks."""

    provider_code = "mtn"


class FlutterwaveWebhookView(BaseWebhookView):
    """Handle Flutterwave webhooks."""

    provider_code = "flutterwave"


class PaystackWebhookView(BaseWebhookView):
    """Handle Paystack webhooks."""

    provider_code = "paystack"


class CinetPayWebhookView(BaseWebhookView):
    """Handle CinetPay webhooks."""

    provider_code = "cinetpay"


class DigitalPayeWebhookView(BaseWebhookView):
    """
    Handle DigitalPaye webhooks.

    DigitalPaye is a unified API for Wave, Orange Money, and MTN Mobile Money.
    A single webhook endpoint handles all three operators.
    """

    provider_code = "digitalpaye"


class CashDrawerSessionViewSet(TenantContextMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing cash drawer sessions.

    GET /api/payments/drawer-sessions/ - List drawer sessions
    GET /api/payments/drawer-sessions/{id}/ - Get session detail
    POST /api/payments/drawer-sessions/open/ - Open a new session
    GET /api/payments/drawer-sessions/current/ - Get current open session
    POST /api/payments/drawer-sessions/{id}/close/ - Close a session
    """

    serializer_class = CashDrawerSessionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        """Get cash drawer sessions filtered by tenant."""
        return CashDrawerSession.objects.all().order_by("-opened_at")

    @action(detail=False, methods=["post"])
    def open(self, request):
        """
        Open a new cash drawer session.

        POST /api/payments/drawer-sessions/open/
        {
            "opening_balance": 50000
        }

        Returns 400 if user already has an open session.
        """
        serializer = OpenDrawerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check if user already has an open session
        existing = CashDrawerSession.objects.filter(
            cashier=request.user,
            closed_at__isnull=True,
        ).first()

        if existing:
            return Response(
                {
                    "detail": "You already have an open cash drawer session.",
                    "session_id": str(existing.id),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create new session
        session = CashDrawerSession.objects.create(
            restaurant=request.user.restaurant,
            cashier=request.user,
            opening_balance=serializer.validated_data["opening_balance"],
        )

        return Response(
            CashDrawerSessionSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def current(self, request):
        """
        Get the current open session for the authenticated user.

        GET /api/payments/drawer-sessions/current/

        Returns 404 if no open session exists.
        """
        session = CashDrawerSession.objects.filter(
            cashier=request.user,
            closed_at__isnull=True,
        ).first()

        if not session:
            return Response(
                {"detail": "No open cash drawer session found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(CashDrawerSessionSerializer(session).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """
        Close a cash drawer session.

        POST /api/payments/drawer-sessions/{id}/close/
        {
            "closing_balance": 60000,
            "variance_notes": "Optional notes"
        }

        Returns 400 if session is already closed.
        Returns 403 if session belongs to another user.
        """
        session = self.get_object()

        # Check session belongs to current user
        if session.cashier_id != request.user.id:
            return Response(
                {"detail": "You can only close your own cash drawer session."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check session is still open
        if not session.is_open:
            return Response(
                {"detail": "This cash drawer session is already closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CloseDrawerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Close the session
        session.close(
            closing_balance=serializer.validated_data["closing_balance"],
            notes=serializer.validated_data.get("variance_notes", ""),
        )
        session.save()

        return Response(CashDrawerSessionSerializer(session).data)


class ReconciliationView(TenantContextMixin, viewsets.GenericViewSet):
    """
    ViewSet for reconciliation reports.

    GET /api/payments/reconciliation/ - Get daily reconciliation report
    GET /api/payments/reconciliation/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD - Range report
    """

    permission_classes = [IsAuthenticated, IsOwnerOrManager]

    def list(self, request):
        """
        Get daily reconciliation report.

        GET /api/payments/reconciliation/?date=2026-02-04
        GET /api/payments/reconciliation/?start_date=2026-02-01&end_date=2026-02-04

        Requires manager or owner role.
        """
        from datetime import datetime

        # Check for date range request
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        if start_date_str and end_date_str:
            # Parse dates
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"detail": "Invalid date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get range report
            try:
                results = get_reconciliation_range(
                    restaurant=request.user.restaurant,
                    start_date=start_date,
                    end_date=end_date,
                )
            except ValueError as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(results)

        # Single date report
        date_str = request.query_params.get("date")
        date = None

        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"detail": "Invalid date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        result = get_daily_reconciliation(
            restaurant=request.user.restaurant,
            date=date,
        )

        return Response(result)
