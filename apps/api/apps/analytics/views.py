"""
Analytics API views for tracking and reporting.
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Count, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import Restaurant
from apps.core.context import get_current_restaurant, set_current_restaurant

from .models import (
    CategoryPerformance,
    CustomerStats,
    DailySalesStats,
    HourlyStats,
    ItemPerformance,
    ReportExport,
    WeeklyReport,
)
from .serializers import (
    AdvancedDashboardSerializer,
    AnalyticsSummarySerializer,
    BenchmarkSerializer,
    CategoryPerformanceSerializer,
    CustomerStatsSerializer,
    DailySalesStatsSerializer,
    HourlyStatsSerializer,
    ItemPerformanceSerializer,
    ReportExportResponseSerializer,
    ReportExportSerializer,
    TrackMenuViewSerializer,
    WeeklyReportSerializer,
)
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


class TenantAnalyticsView(APIView):
    """Base class for tenant-scoped analytics views."""

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

    def get_date_range(self, request):
        """Get date range from query params."""
        days = int(request.query_params.get("days", 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date


class AdvancedDashboardAPI(TenantAnalyticsView):
    """
    Advanced analytics dashboard with comprehensive metrics.

    GET /api/v1/analytics/dashboard/
    Query params: days (default: 30)
    """

    def get(self, request):
        restaurant = get_current_restaurant()
        if not restaurant:
            return Response(
                {"detail": "No restaurant associated with this account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date, end_date = self.get_date_range(request)

        # Get daily stats for the period
        daily_stats = DailySalesStats.objects.filter(
            restaurant=restaurant,
            date__gte=start_date,
            date__lte=end_date,
        )

        # Calculate summary metrics
        totals = daily_stats.aggregate(
            total_revenue=Sum("total_revenue"),
            total_orders=Sum("total_orders"),
            total_items=Sum("total_items_sold"),
        )

        total_revenue = totals["total_revenue"] or 0
        total_orders = totals["total_orders"] or 0
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

        # Get previous period for comparison
        prev_start = start_date - timedelta(days=(end_date - start_date).days)
        prev_stats = DailySalesStats.objects.filter(
            restaurant=restaurant,
            date__gte=prev_start,
            date__lt=start_date,
        ).aggregate(
            total_revenue=Sum("total_revenue"),
            total_orders=Sum("total_orders"),
        )

        prev_revenue = prev_stats["total_revenue"] or 0
        prev_orders = prev_stats["total_orders"] or 0

        revenue_change = (
            ((total_revenue - prev_revenue) / prev_revenue * 100)
            if prev_revenue > 0 else 0
        )
        orders_change = (
            ((total_orders - prev_orders) / prev_orders * 100)
            if prev_orders > 0 else 0
        )

        # Revenue by day
        revenue_by_day = list(
            daily_stats.values("date")
            .annotate(revenue=Sum("total_revenue"), orders=Sum("total_orders"))
            .order_by("date")
        )

        # Orders by type
        orders_by_type = daily_stats.aggregate(
            dine_in=Sum("dine_in_orders"),
            takeaway=Sum("takeaway_orders"),
            delivery=Sum("delivery_orders"),
        )

        # Top items
        top_items = list(
            ItemPerformance.objects.filter(
                restaurant=restaurant,
                date__gte=start_date,
                date__lte=end_date,
            )
            .values("menu_item__id", "menu_item__name")
            .annotate(
                total_quantity=Sum("quantity_sold"),
                total_revenue=Sum("revenue"),
            )
            .order_by("-total_revenue")[:10]
        )

        # Top categories
        top_categories = list(
            CategoryPerformance.objects.filter(
                restaurant=restaurant,
                date__gte=start_date,
                date__lte=end_date,
            )
            .values("category__id", "category__name")
            .annotate(
                total_revenue=Sum("revenue"),
                total_items=Sum("items_sold"),
            )
            .order_by("-total_revenue")[:5]
        )

        # Peak hours (aggregate across period)
        peak_hours = list(
            HourlyStats.objects.filter(
                restaurant=restaurant,
                date__gte=start_date,
                date__lte=end_date,
            )
            .values("hour")
            .annotate(
                total_orders=Sum("order_count"),
                total_revenue=Sum("revenue"),
            )
            .order_by("hour")
        )

        # Customer metrics
        customer_stats = CustomerStats.objects.filter(
            restaurant=restaurant,
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(
            new=Sum("new_customers"),
            returning=Sum("returning_customers"),
            menu_views=Sum("menu_views"),
            orders=Sum("orders_placed"),
        )

        menu_views = customer_stats["menu_views"] or 0
        orders_placed = customer_stats["orders"] or 0
        conversion_rate = (orders_placed / menu_views * 100) if menu_views > 0 else 0

        data = {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "average_order_value": avg_order_value,
            "total_items_sold": totals["total_items"] or 0,
            "revenue_change_percent": round(revenue_change, 2),
            "orders_change_percent": round(orders_change, 2),
            "revenue_by_day": revenue_by_day,
            "orders_by_type": {
                "dine_in": orders_by_type["dine_in"] or 0,
                "takeaway": orders_by_type["takeaway"] or 0,
                "delivery": orders_by_type["delivery"] or 0,
            },
            "top_items": top_items,
            "top_categories": top_categories,
            "peak_hours": peak_hours,
            "conversion_rate": round(conversion_rate, 2),
            "new_vs_returning": {
                "new": customer_stats["new"] or 0,
                "returning": customer_stats["returning"] or 0,
            },
        }

        serializer = AdvancedDashboardSerializer(data)
        return Response(serializer.data)


class SalesStatsAPI(TenantAnalyticsView):
    """
    Daily sales statistics.

    GET /api/v1/analytics/sales/
    Query params: days (default: 30)
    """

    def get(self, request):
        restaurant = get_current_restaurant()
        if not restaurant:
            return Response(
                {"detail": "No restaurant associated with this account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date, end_date = self.get_date_range(request)

        stats = DailySalesStats.objects.filter(
            restaurant=restaurant,
            date__gte=start_date,
            date__lte=end_date,
        ).order_by("-date")

        serializer = DailySalesStatsSerializer(stats, many=True)
        return Response(serializer.data)


class ItemPerformanceAPI(TenantAnalyticsView):
    """
    Item performance rankings.

    GET /api/v1/analytics/items/
    Query params: days (default: 30), limit (default: 20)
    """

    def get(self, request):
        restaurant = get_current_restaurant()
        if not restaurant:
            return Response(
                {"detail": "No restaurant associated with this account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date, end_date = self.get_date_range(request)
        limit = int(request.query_params.get("limit", 20))

        # Aggregate item performance over the period
        items = (
            ItemPerformance.objects.filter(
                restaurant=restaurant,
                date__gte=start_date,
                date__lte=end_date,
            )
            .values("menu_item", "menu_item__name", "menu_item__category__name")
            .annotate(
                total_quantity=Sum("quantity_sold"),
                total_revenue=Sum("revenue"),
            )
            .order_by("-total_revenue")[:limit]
        )

        # Transform for serializer
        result = [
            {
                "menu_item": {
                    "id": item["menu_item"],
                    "name": item["menu_item__name"],
                    "category": {"name": item["menu_item__category__name"]},
                },
                "quantity_sold": item["total_quantity"],
                "revenue": item["total_revenue"],
                "rank_by_quantity": idx + 1,
                "rank_by_revenue": idx + 1,
            }
            for idx, item in enumerate(items)
        ]

        serializer = ItemPerformanceSerializer(result, many=True)
        return Response(serializer.data)


class CategoryPerformanceAPI(TenantAnalyticsView):
    """
    Category performance breakdown.

    GET /api/v1/analytics/categories/
    Query params: days (default: 30)
    """

    def get(self, request):
        restaurant = get_current_restaurant()
        if not restaurant:
            return Response(
                {"detail": "No restaurant associated with this account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date, end_date = self.get_date_range(request)

        # Aggregate category performance
        categories = (
            CategoryPerformance.objects.filter(
                restaurant=restaurant,
                date__gte=start_date,
                date__lte=end_date,
            )
            .values("category", "category__name")
            .annotate(
                total_items=Sum("items_sold"),
                total_revenue=Sum("revenue"),
                total_orders=Sum("order_count"),
            )
            .order_by("-total_revenue")
        )

        # Calculate total for percentages
        total_revenue = sum(c["total_revenue"] or 0 for c in categories)

        result = [
            {
                "category": {
                    "id": cat["category"],
                    "name": cat["category__name"],
                },
                "items_sold": cat["total_items"],
                "revenue": cat["total_revenue"],
                "order_count": cat["total_orders"],
                "revenue_percentage": (
                    round((cat["total_revenue"] or 0) / total_revenue * 100, 2)
                    if total_revenue > 0 else 0
                ),
            }
            for cat in categories
        ]

        serializer = CategoryPerformanceSerializer(result, many=True)
        return Response(serializer.data)


class PeakHoursAPI(TenantAnalyticsView):
    """
    Peak hours analysis.

    GET /api/v1/analytics/peak-hours/
    Query params: days (default: 30)
    """

    def get(self, request):
        restaurant = get_current_restaurant()
        if not restaurant:
            return Response(
                {"detail": "No restaurant associated with this account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date, end_date = self.get_date_range(request)

        # Aggregate hourly stats
        hourly = (
            HourlyStats.objects.filter(
                restaurant=restaurant,
                date__gte=start_date,
                date__lte=end_date,
            )
            .values("hour")
            .annotate(
                total_orders=Sum("order_count"),
                total_revenue=Sum("revenue"),
                total_items=Sum("items_sold"),
            )
            .order_by("hour")
        )

        result = [
            {
                "hour": h["hour"],
                "order_count": h["total_orders"],
                "revenue": h["total_revenue"],
                "items_sold": h["total_items"],
            }
            for h in hourly
        ]

        serializer = HourlyStatsSerializer(result, many=True)
        return Response(serializer.data)


class CustomerAnalyticsAPI(TenantAnalyticsView):
    """
    Customer analytics and conversion funnel.

    GET /api/v1/analytics/customers/
    Query params: days (default: 30)
    """

    def get(self, request):
        restaurant = get_current_restaurant()
        if not restaurant:
            return Response(
                {"detail": "No restaurant associated with this account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date, end_date = self.get_date_range(request)

        stats = CustomerStats.objects.filter(
            restaurant=restaurant,
            date__gte=start_date,
            date__lte=end_date,
        ).order_by("-date")

        serializer = CustomerStatsSerializer(stats, many=True)
        return Response(serializer.data)


class WeeklyReportsAPI(TenantAnalyticsView):
    """
    Weekly reports list and details.

    GET /api/v1/analytics/weekly-reports/
    """

    def get(self, request):
        restaurant = get_current_restaurant()
        if not restaurant:
            return Response(
                {"detail": "No restaurant associated with this account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reports = WeeklyReport.objects.filter(
            restaurant=restaurant,
        ).order_by("-week_start")[:12]

        serializer = WeeklyReportSerializer(reports, many=True)
        return Response(serializer.data)


class ExportReportAPI(TenantAnalyticsView):
    """
    Export analytics reports to CSV/PDF.

    POST /api/v1/analytics/export/
    """

    def post(self, request):
        restaurant = get_current_restaurant()
        if not restaurant:
            return Response(
                {"detail": "No restaurant associated with this account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReportExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create export record
        export = ReportExport.objects.create(
            restaurant=restaurant,
            export_type=serializer.validated_data["export_type"],
            format=serializer.validated_data["format"],
            date_from=serializer.validated_data["date_from"],
            date_to=serializer.validated_data["date_to"],
            requested_by=request.user,
            status="pending",
        )

        # In production, this would trigger a Celery task
        # For now, we return the pending export
        response_data = {
            "id": export.id,
            "export_type": export.export_type,
            "format": export.format,
            "date_from": export.date_from,
            "date_to": export.date_to,
            "status": export.status,
            "file_url": None,
            "file_size": 0,
            "created_at": export.created_at,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class BenchmarkAPI(TenantAnalyticsView):
    """
    Compare metrics against industry benchmarks.

    GET /api/v1/analytics/benchmarks/
    """

    def get(self, request):
        restaurant = get_current_restaurant()
        if not restaurant:
            return Response(
                {"detail": "No restaurant associated with this account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date, end_date = self.get_date_range(request)

        # Get restaurant metrics
        stats = DailySalesStats.objects.filter(
            restaurant=restaurant,
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(
            avg_daily_orders=Avg("total_orders"),
            avg_order_value=Avg("average_order_value"),
            total_revenue=Sum("total_revenue"),
        )

        # Industry benchmarks (placeholder values)
        # In production, these would come from aggregated data
        benchmarks = [
            {
                "metric": "Average Daily Orders",
                "your_value": stats["avg_daily_orders"] or 0,
                "industry_average": 45,
                "percentile": self._calculate_percentile(
                    stats["avg_daily_orders"] or 0, 45
                ),
                "status": self._get_status(stats["avg_daily_orders"] or 0, 45),
            },
            {
                "metric": "Average Order Value (XOF)",
                "your_value": stats["avg_order_value"] or 0,
                "industry_average": 4500,
                "percentile": self._calculate_percentile(
                    stats["avg_order_value"] or 0, 4500
                ),
                "status": self._get_status(stats["avg_order_value"] or 0, 4500),
            },
            {
                "metric": "Delivery Order %",
                "your_value": 25,  # Placeholder
                "industry_average": 30,
                "percentile": 40,
                "status": "average",
            },
            {
                "metric": "Menu Items",
                "your_value": 35,  # Placeholder
                "industry_average": 40,
                "percentile": 45,
                "status": "average",
            },
        ]

        serializer = BenchmarkSerializer(benchmarks, many=True)
        return Response(serializer.data)

    def _calculate_percentile(self, value, benchmark):
        """Simple percentile calculation."""
        if benchmark == 0:
            return 50
        ratio = value / benchmark
        if ratio >= 1.5:
            return 90
        elif ratio >= 1.2:
            return 75
        elif ratio >= 0.8:
            return 50
        elif ratio >= 0.5:
            return 25
        return 10

    def _get_status(self, value, benchmark):
        """Get status compared to benchmark."""
        if benchmark == 0:
            return "average"
        ratio = value / benchmark
        if ratio >= 1.1:
            return "above"
        elif ratio >= 0.9:
            return "average"
        return "below"
