"""
Analytics models for tracking menu views, orders, revenue, and business insights.
"""
from django.db import models
from django.utils import timezone

from apps.core.managers import TenantManager
from apps.core.models import TenantModel


class MenuView(TenantModel):
    """
    Individual menu view event.

    Tracks when a customer views a business's public menu.
    """

    SOURCE_CHOICES = [
        ("qr", "QR Code"),
        ("link", "Direct Link"),
        ("whatsapp", "WhatsApp"),
        ("other", "Other"),
    ]

    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    session_id = models.CharField(
        max_length=100,
        help_text="Client-generated session ID for unique visitor tracking",
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default="link",
        help_text="How the customer accessed the menu",
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        help_text="Browser/device user agent string",
    )

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-viewed_at"]
        indexes = [
            models.Index(fields=["business", "viewed_at"]),
            models.Index(fields=["business", "session_id"]),
        ]

    def __str__(self):
        return f"Menu view for {self.business} at {self.viewed_at}"


class DailyMenuStats(TenantModel):
    """
    Aggregated daily statistics for menu views.

    Pre-computed for efficient dashboard queries.
    """

    date = models.DateField(db_index=True)
    total_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    qr_scans = models.PositiveIntegerField(default=0)
    top_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of most viewed item IDs (if item-level tracking added)",
    )

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-date"]
        unique_together = [("business", "date")]
        verbose_name_plural = "Daily menu stats"
        indexes = [
            models.Index(fields=["business", "date"]),
        ]

    def __str__(self):
        return f"Stats for {self.business} on {self.date}"


class DailySalesStats(TenantModel):
    """
    Aggregated daily sales statistics.
    """

    date = models.DateField(db_index=True)

    # Order counts
    total_orders = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    cancelled_orders = models.PositiveIntegerField(default=0)

    # Order types
    dine_in_orders = models.PositiveIntegerField(default=0)
    takeaway_orders = models.PositiveIntegerField(default=0)
    delivery_orders = models.PositiveIntegerField(default=0)

    # Revenue
    total_revenue = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    # Items
    total_items_sold = models.PositiveIntegerField(default=0)

    # Peak hours (JSON: {hour: count})
    orders_by_hour = models.JSONField(default=dict, blank=True)

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-date"]
        unique_together = [("business", "date")]
        verbose_name_plural = "Daily sales stats"
        indexes = [
            models.Index(fields=["business", "date"]),
        ]

    def __str__(self):
        return f"Sales for {self.business} on {self.date}"


class ItemPerformance(TenantModel):
    """
    Performance metrics for individual menu items over time.
    """

    menu_item = models.ForeignKey(
        "menu.Product",
        on_delete=models.CASCADE,
        related_name="performance_stats",
    )
    date = models.DateField(db_index=True)

    # Sales metrics
    quantity_sold = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    # Rankings (computed daily)
    rank_by_quantity = models.PositiveIntegerField(null=True, blank=True)
    rank_by_revenue = models.PositiveIntegerField(null=True, blank=True)

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-date", "-quantity_sold"]
        unique_together = [("business", "menu_item", "date")]
        indexes = [
            models.Index(fields=["business", "date"]),
            models.Index(fields=["menu_item", "date"]),
        ]

    def __str__(self):
        return f"{self.menu_item.name} on {self.date}"


class CategoryPerformance(TenantModel):
    """
    Performance metrics for menu categories.
    """

    category = models.ForeignKey(
        "menu.Category",
        on_delete=models.CASCADE,
        related_name="performance_stats",
    )
    date = models.DateField(db_index=True)

    # Sales metrics
    items_sold = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    order_count = models.PositiveIntegerField(default=0)

    # Percentage of total
    revenue_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-date", "-revenue"]
        unique_together = [("business", "category", "date")]
        indexes = [
            models.Index(fields=["business", "date"]),
        ]

    def __str__(self):
        return f"{self.category.name} on {self.date}"


class HourlyStats(TenantModel):
    """
    Hourly breakdown for peak hours analysis.
    """

    date = models.DateField(db_index=True)
    hour = models.PositiveSmallIntegerField()  # 0-23

    order_count = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    items_sold = models.PositiveIntegerField(default=0)

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-date", "hour"]
        unique_together = [("business", "date", "hour")]
        indexes = [
            models.Index(fields=["business", "date"]),
        ]

    def __str__(self):
        return f"{self.business} on {self.date} at {self.hour}:00"


class CustomerStats(TenantModel):
    """
    Customer-related analytics.
    """

    date = models.DateField(db_index=True)

    # Customer counts
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    total_customers = models.PositiveIntegerField(default=0)

    # Conversion metrics
    menu_views = models.PositiveIntegerField(default=0)
    orders_placed = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Percentage of menu views that resulted in orders"
    )

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-date"]
        unique_together = [("business", "date")]
        indexes = [
            models.Index(fields=["business", "date"]),
        ]

    def __str__(self):
        return f"Customer stats for {self.business} on {self.date}"


class WeeklyReport(TenantModel):
    """
    Pre-computed weekly reports for automated delivery.
    """

    week_start = models.DateField(db_index=True)
    week_end = models.DateField()

    # Summary metrics
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    average_daily_revenue = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    # Comparisons with previous week
    orders_change_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    revenue_change_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )

    # Top items (JSON list)
    top_items = models.JSONField(default=list, blank=True)

    # Peak hours (JSON: {hour: count})
    peak_hours = models.JSONField(default=dict, blank=True)

    # Report content (pre-rendered for email)
    report_html = models.TextField(blank=True)

    # Delivery status
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_to = models.JSONField(default=list, blank=True)

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-week_start"]
        unique_together = [("business", "week_start")]
        indexes = [
            models.Index(fields=["business", "week_start"]),
        ]

    def __str__(self):
        return f"Weekly report for {self.business}: {self.week_start} to {self.week_end}"


class ReportExport(TenantModel):
    """
    Track exported reports (CSV, PDF).
    """

    EXPORT_TYPE_CHOICES = [
        ("sales", "Sales Report"),
        ("items", "Item Performance"),
        ("categories", "Category Performance"),
        ("customers", "Customer Analytics"),
        ("hourly", "Hourly Breakdown"),
        ("full", "Full Report"),
    ]

    FORMAT_CHOICES = [
        ("csv", "CSV"),
        ("pdf", "PDF"),
        ("xlsx", "Excel"),
    ]

    export_type = models.CharField(max_length=20, choices=EXPORT_TYPE_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    date_from = models.DateField()
    date_to = models.DateField()

    # File info
    file = models.FileField(upload_to="analytics/exports/", null=True, blank=True)
    file_size = models.PositiveIntegerField(default=0)

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    error_message = models.TextField(blank=True)

    # Requested by
    requested_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_exports",
    )

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_export_type_display()} ({self.format}) - {self.date_from} to {self.date_to}"
