"""URL configuration for reservations app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AvailabilityView,
    BusinessHoursViewSet,
    DailySummaryView,
    PublicAvailabilityView,
    PublicCancelReservationView,
    PublicCreateReservationView,
    PublicReservationLookupView,
    ReservationSettingsView,
    ReservationViewSet,
    SpecialHoursViewSet,
    TableConfigurationViewSet,
    UpcomingReservationsView,
    WaitlistViewSet,
)

router = DefaultRouter()
router.register("tables", TableConfigurationViewSet, basename="table")
router.register("business-hours", BusinessHoursViewSet, basename="business-hours")
router.register("special-hours", SpecialHoursViewSet, basename="special-hours")
router.register("reservations", ReservationViewSet, basename="reservation")
router.register("waitlist", WaitlistViewSet, basename="waitlist")

urlpatterns = [
    # Settings
    path("settings/", ReservationSettingsView.as_view(), name="reservation-settings"),

    # Availability
    path("availability/", AvailabilityView.as_view(), name="availability"),

    # Summary
    path("summary/", DailySummaryView.as_view(), name="daily-summary"),
    path("upcoming/", UpcomingReservationsView.as_view(), name="upcoming-reservations"),

    # Public endpoints
    path("public/<slug:slug>/availability/", PublicAvailabilityView.as_view(), name="public-availability"),
    path("public/<slug:slug>/book/", PublicCreateReservationView.as_view(), name="public-book"),
    path("public/<slug:slug>/lookup/<str:code>/", PublicReservationLookupView.as_view(), name="public-lookup"),
    path("public/<slug:slug>/cancel/<str:code>/", PublicCancelReservationView.as_view(), name="public-cancel"),

    # Router URLs
    path("", include(router.urls)),
]
