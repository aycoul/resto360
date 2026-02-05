"""Services for reservation availability and management."""

from datetime import date, datetime, time, timedelta
from typing import Optional

from django.db.models import Q, Sum

from .models import (
    BusinessHours,
    Reservation,
    ReservationSettings,
    ReservationStatus,
    SpecialHours,
    TableConfiguration,
)


class AvailabilityService:
    """Service for checking and managing table availability."""

    def __init__(self, business):
        self.business = business
        self._settings = None
        self._tables = None

    @property
    def settings(self) -> Optional[ReservationSettings]:
        """Get or create reservation settings."""
        if self._settings is None:
            self._settings, _ = ReservationSettings.objects.get_or_create(
                business=self.business
            )
        return self._settings

    @property
    def tables(self):
        """Get active tables."""
        if self._tables is None:
            self._tables = list(
                TableConfiguration.objects.filter(
                    business=self.business,
                    is_active=True,
                )
            )
        return self._tables

    def get_business_hours(self, target_date: date) -> list[dict]:
        """
        Get business hours for a specific date.

        Checks for special hours first, then falls back to regular hours.
        """
        # Check for special hours
        special = SpecialHours.objects.filter(
            business=self.business,
            date=target_date,
        ).first()

        if special:
            if special.is_closed:
                return []
            return [{
                "open_time": special.open_time,
                "close_time": special.close_time,
                "last_seating": special.close_time,
            }]

        # Get regular hours for this day of week
        day_of_week = target_date.weekday()
        hours = BusinessHours.objects.filter(
            business=self.business,
            day_of_week=day_of_week,
            is_open=True,
        )

        return [
            {
                "open_time": h.open_time,
                "close_time": h.close_time,
                "last_seating": h.last_seating_time or h.close_time,
            }
            for h in hours
        ]

    def get_time_slots(self, target_date: date) -> list[time]:
        """
        Generate available time slots for a date.

        Returns list of times based on business hours and slot duration.
        """
        hours_list = self.get_business_hours(target_date)
        if not hours_list:
            return []

        slot_duration = timedelta(minutes=self.settings.slot_duration_minutes)
        slots = []

        for hours in hours_list:
            current = datetime.combine(target_date, hours["open_time"])
            last_seating = datetime.combine(target_date, hours["last_seating"])

            while current <= last_seating:
                slots.append(current.time())
                current += slot_duration

        return slots

    def get_existing_reservations(
        self,
        target_date: date,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
    ) -> list[Reservation]:
        """Get active reservations for a date/time range."""
        qs = Reservation.objects.filter(
            business=self.business,
            date=target_date,
            status__in=[
                ReservationStatus.PENDING,
                ReservationStatus.CONFIRMED,
                ReservationStatus.SEATED,
            ],
        )

        if start_time:
            qs = qs.filter(time__gte=start_time)
        if end_time:
            qs = qs.filter(time__lte=end_time)

        return list(qs)

    def check_table_availability(
        self,
        target_date: date,
        target_time: time,
        party_size: int,
        duration_minutes: int = 90,
        exclude_reservation_id: Optional[str] = None,
    ) -> list[TableConfiguration]:
        """
        Find available tables for a specific date/time/party size.

        Returns list of tables that can accommodate the party.
        """
        # Get tables that can fit the party
        suitable_tables = [
            t for t in self.tables
            if t.min_capacity <= party_size <= t.capacity
        ]

        if not suitable_tables:
            return []

        # Calculate time window
        booking_start = datetime.combine(target_date, target_time)
        booking_end = booking_start + timedelta(minutes=duration_minutes)

        # Get overlapping reservations
        existing = self.get_existing_reservations(target_date)

        # Filter out excluded reservation (for modifications)
        if exclude_reservation_id:
            existing = [r for r in existing if str(r.id) != exclude_reservation_id]

        # Find occupied tables
        occupied_table_ids = set()
        for reservation in existing:
            res_start = datetime.combine(reservation.date, reservation.time)
            res_end = res_start + timedelta(minutes=reservation.duration_minutes)

            # Check for overlap
            if res_start < booking_end and res_end > booking_start:
                if reservation.table_id:
                    occupied_table_ids.add(reservation.table_id)

        # Return available tables
        return [t for t in suitable_tables if t.id not in occupied_table_ids]

    def get_availability(
        self,
        target_date: date,
        party_size: int,
    ) -> list[dict]:
        """
        Get all available time slots with table counts for a date.

        Returns list of slot info with availability.
        """
        slots = self.get_time_slots(target_date)
        if not slots:
            return []

        # Check minimum advance time
        if target_date == date.today():
            min_time = (
                datetime.now() + timedelta(hours=self.settings.min_advance_hours)
            ).time()
            slots = [s for s in slots if s >= min_time]

        result = []
        for slot_time in slots:
            available_tables = self.check_table_availability(
                target_date,
                slot_time,
                party_size,
                self.settings.default_dining_duration_minutes,
            )

            if available_tables:
                result.append({
                    "time": slot_time,
                    "available_tables": len(available_tables),
                    "max_party_size": max(t.capacity for t in available_tables),
                })

        return result

    def auto_assign_table(
        self,
        target_date: date,
        target_time: time,
        party_size: int,
        duration_minutes: int = 90,
    ) -> Optional[TableConfiguration]:
        """
        Automatically assign the best table for a reservation.

        Prefers tables that closely match party size to optimize seating.
        """
        available = self.check_table_availability(
            target_date,
            target_time,
            party_size,
            duration_minutes,
        )

        if not available:
            return None

        # Sort by capacity (prefer smallest table that fits)
        available.sort(key=lambda t: t.capacity)
        return available[0]


class ReservationService:
    """Service for reservation operations."""

    def __init__(self, business):
        self.business = business
        self.availability = AvailabilityService(business)

    def create_reservation(
        self,
        date: date,
        time: time,
        party_size: int,
        customer_name: str,
        customer_phone: str = "",
        customer_email: str = "",
        special_requests: str = "",
        occasion: str = "",
        source: str = "online",
        auto_confirm: bool = False,
    ) -> Reservation:
        """Create a new reservation."""
        settings = self.availability.settings

        # Auto-assign table
        table = self.availability.auto_assign_table(
            date,
            time,
            party_size,
            settings.default_dining_duration_minutes,
        )

        # Determine initial status
        status = (
            ReservationStatus.CONFIRMED
            if auto_confirm or not settings.confirmation_required
            else ReservationStatus.PENDING
        )

        reservation = Reservation.objects.create(
            business=self.business,
            date=date,
            time=time,
            party_size=party_size,
            duration_minutes=settings.default_dining_duration_minutes,
            table=table,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            special_requests=special_requests,
            occasion=occasion,
            source=source,
            status=status,
        )

        return reservation

    def get_daily_summary(self, target_date: date) -> dict:
        """Get summary of reservations for a day."""
        reservations = Reservation.objects.filter(
            business=self.business,
            date=target_date,
        )

        total = reservations.count()
        guests = reservations.aggregate(total=Sum("party_size"))["total"] or 0

        return {
            "date": target_date,
            "total_reservations": total,
            "total_guests": guests,
            "confirmed": reservations.filter(
                status=ReservationStatus.CONFIRMED
            ).count(),
            "pending": reservations.filter(status=ReservationStatus.PENDING).count(),
            "seated": reservations.filter(status=ReservationStatus.SEATED).count(),
            "cancelled": reservations.filter(
                status=ReservationStatus.CANCELLED
            ).count(),
            "no_shows": reservations.filter(status=ReservationStatus.NO_SHOW).count(),
        }

    def get_upcoming_reservations(self, days: int = 7) -> list[Reservation]:
        """Get upcoming reservations for the next N days."""
        today = date.today()
        end_date = today + timedelta(days=days)

        return list(
            Reservation.objects.filter(
                business=self.business,
                date__gte=today,
                date__lte=end_date,
                status__in=[
                    ReservationStatus.PENDING,
                    ReservationStatus.CONFIRMED,
                ],
            ).order_by("date", "time")
        )
