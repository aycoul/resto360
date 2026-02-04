"""
Serializers for analytics API endpoints.
"""
from rest_framework import serializers


class TrackMenuViewSerializer(serializers.Serializer):
    """Serializer for tracking menu view events."""

    restaurant_slug = serializers.SlugField(
        max_length=200,
        help_text="Slug of the restaurant menu being viewed",
    )
    session_id = serializers.CharField(
        max_length=100,
        help_text="Client-generated session identifier",
    )
    source = serializers.ChoiceField(
        choices=["qr", "link", "whatsapp", "other"],
        default="link",
        help_text="How the menu was accessed",
    )
    user_agent = serializers.CharField(
        max_length=500,
        required=False,
        default="",
        allow_blank=True,
        help_text="Browser/device user agent",
    )


class AnalyticsSummarySerializer(serializers.Serializer):
    """Serializer for analytics summary response."""

    views_today = serializers.IntegerField()
    views_week = serializers.IntegerField()
    views_month = serializers.IntegerField()
    unique_today = serializers.IntegerField()
    menu_items = serializers.IntegerField()


class DailySalesStatsSerializer(serializers.Serializer):
    """Serializer for daily sales statistics."""

    date = serializers.DateField()
    total_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    dine_in_orders = serializers.IntegerField()
    takeaway_orders = serializers.IntegerField()
    delivery_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=0)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=0)
    total_items_sold = serializers.IntegerField()
    orders_by_hour = serializers.JSONField()


class ItemPerformanceSerializer(serializers.Serializer):
    """Serializer for item performance data."""

    id = serializers.UUIDField(source="menu_item.id")
    name = serializers.CharField(source="menu_item.name")
    category = serializers.CharField(source="menu_item.category.name")
    quantity_sold = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=0)
    rank_by_quantity = serializers.IntegerField(allow_null=True)
    rank_by_revenue = serializers.IntegerField(allow_null=True)


class CategoryPerformanceSerializer(serializers.Serializer):
    """Serializer for category performance data."""

    id = serializers.UUIDField(source="category.id")
    name = serializers.CharField(source="category.name")
    items_sold = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=0)
    order_count = serializers.IntegerField()
    revenue_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class HourlyStatsSerializer(serializers.Serializer):
    """Serializer for hourly statistics."""

    hour = serializers.IntegerField()
    order_count = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=0)
    items_sold = serializers.IntegerField()


class CustomerStatsSerializer(serializers.Serializer):
    """Serializer for customer statistics."""

    date = serializers.DateField()
    new_customers = serializers.IntegerField()
    returning_customers = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    menu_views = serializers.IntegerField()
    orders_placed = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class WeeklyReportSerializer(serializers.Serializer):
    """Serializer for weekly report data."""

    id = serializers.UUIDField()
    week_start = serializers.DateField()
    week_end = serializers.DateField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=0)
    average_daily_revenue = serializers.DecimalField(max_digits=10, decimal_places=0)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=0)
    orders_change_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    revenue_change_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    top_items = serializers.JSONField()
    peak_hours = serializers.JSONField()
    sent_at = serializers.DateTimeField(allow_null=True)


class ReportExportSerializer(serializers.Serializer):
    """Serializer for report export requests."""

    export_type = serializers.ChoiceField(
        choices=["sales", "items", "categories", "customers", "hourly", "full"]
    )
    format = serializers.ChoiceField(choices=["csv", "pdf", "xlsx"])
    date_from = serializers.DateField()
    date_to = serializers.DateField()


class ReportExportResponseSerializer(serializers.Serializer):
    """Serializer for export response."""

    id = serializers.UUIDField()
    export_type = serializers.CharField()
    format = serializers.CharField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    status = serializers.CharField()
    file_url = serializers.URLField(allow_null=True)
    file_size = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class AdvancedDashboardSerializer(serializers.Serializer):
    """Serializer for advanced analytics dashboard."""

    # Summary metrics
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=0)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=0)
    total_items_sold = serializers.IntegerField()

    # Comparison with previous period
    revenue_change_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    orders_change_percent = serializers.DecimalField(max_digits=5, decimal_places=2)

    # Breakdowns
    revenue_by_day = serializers.ListField(child=serializers.DictField())
    orders_by_type = serializers.DictField()
    top_items = serializers.ListField(child=serializers.DictField())
    top_categories = serializers.ListField(child=serializers.DictField())
    peak_hours = serializers.ListField(child=serializers.DictField())

    # Customer metrics
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    new_vs_returning = serializers.DictField()


class BenchmarkSerializer(serializers.Serializer):
    """Serializer for industry benchmark comparison."""

    metric = serializers.CharField()
    your_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    industry_average = serializers.DecimalField(max_digits=10, decimal_places=2)
    percentile = serializers.IntegerField()
    status = serializers.ChoiceField(choices=["above", "average", "below"])
