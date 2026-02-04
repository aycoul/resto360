"""
Analytics API views for tracking and reporting.
"""
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import Restaurant
from apps.core.context import get_current_restaurant, set_current_restaurant

from .serializers import AnalyticsSummarySerializer, TrackMenuViewSerializer
from .services import get_analytics_summary, track_menu_view


class TrackMenuViewAPI(APIView):
    """
    Public endpoint for tracking menu view events.

    POST /api/v1/analytics/track/
    No authentication required - called from public menu page.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """
        Track a menu view event.

        Request body:
        {
            "restaurant_slug": "demo-restaurant",
            "session_id": "abc123-xyz789",
            "source": "qr",
            "user_agent": "Mozilla/5.0..."
        }
        """
        serializer = TrackMenuViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Find the restaurant by slug
        try:
            restaurant = Restaurant.objects.get(
                slug=serializer.validated_data["restaurant_slug"],
                is_active=True,
            )
        except Restaurant.DoesNotExist:
            return Response(
                {"detail": "Restaurant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Record the view
        track_menu_view(
            restaurant=restaurant,
            session_id=serializer.validated_data["session_id"],
            source=serializer.validated_data.get("source", "link"),
            user_agent=serializer.validated_data.get("user_agent", ""),
        )

        return Response({"status": "tracked"}, status=status.HTTP_201_CREATED)


class AnalyticsSummaryAPI(APIView):
    """
    Authenticated endpoint for getting analytics summary.

    GET /api/v1/analytics/summary/
    Requires authentication - returns stats for user's restaurant.
    """

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
        Get analytics summary for the authenticated user's restaurant.

        Returns:
        {
            "views_today": 42,
            "views_week": 156,
            "views_month": 520,
            "unique_today": 35,
            "menu_items": 18
        }
        """
        restaurant = get_current_restaurant()

        if not restaurant:
            return Response(
                {"detail": "No restaurant associated with this account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        summary = get_analytics_summary(restaurant)
        serializer = AnalyticsSummarySerializer(summary)

        return Response(serializer.data, status=status.HTTP_200_OK)
