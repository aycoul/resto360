"""Views for reservations app."""

from datetime import date, timedelta

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import Restaurant

from .models import (
    BusinessHours,
    Reservation,
    ReservationSettings,
    ReservationSource,
    ReservationStatus,
    SpecialHours,
    TableConfiguration,
    Waitlist,
)
from .serializers import (
    AvailabilityRequestSerializer,
    BusinessHoursSerializer,
    CreateReservationSerializer,
    CreateWaitlistSerializer,
    PublicCreateReservationSerializer,
    ReservationSerializer,
    ReservationSettingsSerializer,
    ReservationStatusUpdateSerializer,
    SpecialHoursSerializer,
    TableConfigurationSerializer,
    WaitlistSerializer,
)
from .services import AvailabilityService, ReservationService


class TableConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tables."""

    serializer_class = TableConfigurationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TableConfiguration.objects.filter(restaurant=self.request.user.restaurant)

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


class BusinessHoursViewSet(viewsets.ModelViewSet):
    """ViewSet for managing business hours."""

    serializer_class = BusinessHoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BusinessHours.objects.filter(restaurant=self.request.user.restaurant)

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


class SpecialHoursViewSet(viewsets.ModelViewSet):
    """ViewSet for managing special hours."""

    serializer_class = SpecialHoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SpecialHours.objects.filter(
            restaurant=self.request.user.restaurant,
            date__gte=date.today(),
        )

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


class ReservationSettingsView(APIView):
    """View for managing reservation settings."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings, _ = ReservationSettings.objects.get_or_create(
            restaurant=request.user.restaurant
        )
        serializer = ReservationSettingsSerializer(settings)
        return Response(serializer.data)

    def patch(self, request):
        settings, _ = ReservationSettings.objects.get_or_create(
            restaurant=request.user.restaurant
        )
        serializer = ReservationSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ReservationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reservations."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateReservationSerializer
        return ReservationSerializer

    def get_queryset(self):
        qs = Reservation.objects.filter(restaurant=self.request.user.restaurant)

        # Filter by date
        date_str = self.request.query_params.get("date")
        if date_str:
            try:
                filter_date = date.fromisoformat(date_str)
                qs = qs.filter(date=filter_date)
            except ValueError:
                pass

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Filter by date range
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        return qs.order_by("date", "time")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        settings, _ = ReservationSettings.objects.get_or_create(
            restaurant=self.request.user.restaurant
        )
        context["settings"] = settings
        return context

    def perform_create(self, serializer):
        service = ReservationService(self.request.user.restaurant)
        data = serializer.validated_data

        reservation = service.create_reservation(
            date=data["date"],
            time=data["time"],
            party_size=data["party_size"],
            customer_name=data["customer_name"],
            customer_phone=data.get("customer_phone", ""),
            customer_email=data.get("customer_email", ""),
            special_requests=data.get("special_requests", ""),
            occasion=data.get("occasion", ""),
            source=ReservationSource.PHONE,  # Created by staff
        )

        serializer.instance = reservation

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm a pending reservation."""
        reservation = self.get_object()
        if reservation.status != ReservationStatus.PENDING:
            return Response(
                {"error": "Only pending reservations can be confirmed"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reservation.confirm()
        return Response(ReservationSerializer(reservation).data)

    @action(detail=True, methods=["post"])
    def seat(self, request, pk=None):
        """Mark reservation as seated."""
        reservation = self.get_object()
        if reservation.status not in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
            return Response(
                {"error": "Cannot seat this reservation"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reservation.seat()
        return Response(ReservationSerializer(reservation).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark reservation as completed."""
        reservation = self.get_object()
        if reservation.status != ReservationStatus.SEATED:
            return Response(
                {"error": "Only seated reservations can be completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reservation.complete()
        return Response(ReservationSerializer(reservation).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a reservation."""
        reservation = self.get_object()
        if reservation.status in [ReservationStatus.COMPLETED, ReservationStatus.CANCELLED]:
            return Response(
                {"error": "Cannot cancel this reservation"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reason = request.data.get("reason", "")
        reservation.cancel(reason)
        return Response(ReservationSerializer(reservation).data)

    @action(detail=True, methods=["post"])
    def no_show(self, request, pk=None):
        """Mark reservation as no-show."""
        reservation = self.get_object()
        if reservation.status not in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
            return Response(
                {"error": "Cannot mark this reservation as no-show"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reservation.mark_no_show()
        return Response(ReservationSerializer(reservation).data)


class AvailabilityView(APIView):
    """Check reservation availability."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AvailabilityRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_date = serializer.validated_data["date"]
        party_size = serializer.validated_data["party_size"]

        service = AvailabilityService(request.user.restaurant)
        slots = service.get_availability(target_date, party_size)

        return Response({
            "date": target_date,
            "party_size": party_size,
            "slots": slots,
            "is_available": len(slots) > 0,
        })


class DailySummaryView(APIView):
    """Get daily reservation summary."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.query_params.get("date")
        try:
            target_date = date.fromisoformat(date_str) if date_str else date.today()
        except ValueError:
            return Response(
                {"error": "Invalid date format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = ReservationService(request.user.restaurant)
        summary = service.get_daily_summary(target_date)
        return Response(summary)


class UpcomingReservationsView(APIView):
    """Get upcoming reservations."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 7))
        service = ReservationService(request.user.restaurant)
        reservations = service.get_upcoming_reservations(days)
        return Response(ReservationSerializer(reservations, many=True).data)


class WaitlistViewSet(viewsets.ModelViewSet):
    """ViewSet for managing waitlist."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateWaitlistSerializer
        return WaitlistSerializer

    def get_queryset(self):
        return Waitlist.objects.filter(
            restaurant=self.request.user.restaurant,
            created_at__date=date.today(),
            is_cancelled=False,
            is_seated=False,
        ).order_by("created_at")

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)

    @action(detail=True, methods=["post"])
    def notify(self, request, pk=None):
        """Mark customer as notified."""
        entry = self.get_object()
        entry.notify()
        return Response(WaitlistSerializer(entry).data)

    @action(detail=True, methods=["post"])
    def seat(self, request, pk=None):
        """Seat the customer."""
        entry = self.get_object()
        entry.seat()
        return Response(WaitlistSerializer(entry).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel waitlist entry."""
        entry = self.get_object()
        entry.cancel()
        return Response(WaitlistSerializer(entry).data)


# Public endpoints (no auth required)


class PublicAvailabilityView(APIView):
    """Public endpoint to check availability."""

    permission_classes = [AllowAny]

    def post(self, request, slug):
        try:
            restaurant = Restaurant.objects.get(slug=slug)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AvailabilityRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_date = serializer.validated_data["date"]
        party_size = serializer.validated_data["party_size"]

        service = AvailabilityService(restaurant)
        slots = service.get_availability(target_date, party_size)

        return Response({
            "date": target_date,
            "party_size": party_size,
            "slots": slots,
            "is_available": len(slots) > 0,
        })


class PublicCreateReservationView(APIView):
    """Public endpoint to create reservations."""

    permission_classes = [AllowAny]

    def post(self, request, slug):
        try:
            restaurant = Restaurant.objects.get(slug=slug)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        settings, _ = ReservationSettings.objects.get_or_create(restaurant=restaurant)

        serializer = PublicCreateReservationSerializer(
            data=request.data,
            context={"settings": settings},
        )
        serializer.is_valid(raise_exception=True)

        service = ReservationService(restaurant)
        data = serializer.validated_data

        # Check availability
        availability = AvailabilityService(restaurant)
        available_tables = availability.check_table_availability(
            data["date"],
            data["time"],
            data["party_size"],
        )

        if not available_tables:
            return Response(
                {"error": "No tables available for this time slot"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reservation = service.create_reservation(
            date=data["date"],
            time=data["time"],
            party_size=data["party_size"],
            customer_name=data["customer_name"],
            customer_phone=data.get("customer_phone", ""),
            customer_email=data.get("customer_email", ""),
            special_requests=data.get("special_requests", ""),
            occasion=data.get("occasion", ""),
            source=ReservationSource.ONLINE,
        )

        return Response({
            "id": str(reservation.id),
            "confirmation_code": reservation.confirmation_code,
            "date": reservation.date,
            "time": reservation.time,
            "party_size": reservation.party_size,
            "status": reservation.status,
            "message": "Reservation created successfully",
        }, status=status.HTTP_201_CREATED)


class PublicReservationLookupView(APIView):
    """Public endpoint to look up a reservation."""

    permission_classes = [AllowAny]

    def get(self, request, slug, code):
        try:
            restaurant = Restaurant.objects.get(slug=slug)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            reservation = Reservation.all_objects.get(
                restaurant=restaurant,
                confirmation_code=code.upper(),
            )
        except Reservation.DoesNotExist:
            return Response(
                {"error": "Reservation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            "id": str(reservation.id),
            "confirmation_code": reservation.confirmation_code,
            "date": reservation.date,
            "time": reservation.time,
            "party_size": reservation.party_size,
            "customer_name": reservation.customer_name,
            "status": reservation.status,
            "status_display": reservation.get_status_display(),
            "table_name": reservation.table.name if reservation.table else None,
            "special_requests": reservation.special_requests,
            "occasion": reservation.occasion,
        })


class PublicCancelReservationView(APIView):
    """Public endpoint to cancel a reservation."""

    permission_classes = [AllowAny]

    def post(self, request, slug, code):
        try:
            restaurant = Restaurant.objects.get(slug=slug)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            reservation = Reservation.all_objects.get(
                restaurant=restaurant,
                confirmation_code=code.upper(),
            )
        except Reservation.DoesNotExist:
            return Response(
                {"error": "Reservation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if reservation.status in [ReservationStatus.COMPLETED, ReservationStatus.CANCELLED]:
            return Response(
                {"error": "Cannot cancel this reservation"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check cancellation deadline
        settings, _ = ReservationSettings.objects.get_or_create(restaurant=restaurant)
        from datetime import datetime
        from django.utils import timezone

        reservation_dt = datetime.combine(reservation.date, reservation.time)
        deadline = reservation_dt - timedelta(hours=settings.cancellation_hours)

        if datetime.now() > deadline:
            return Response(
                {"error": f"Cancellations must be made at least {settings.cancellation_hours} hours before"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("reason", "Cancelled by customer")
        reservation.cancel(reason)

        return Response({
            "message": "Reservation cancelled successfully",
            "confirmation_code": reservation.confirmation_code,
        })
