"""ViewSets for payment API endpoints."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.views import TenantContextMixin

from .models import CashDrawerSession, PaymentMethod
from .serializers import (
    CashDrawerSessionSerializer,
    CloseDrawerSerializer,
    OpenDrawerSerializer,
    PaymentMethodSerializer,
)


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
