"""
Analytics models for tracking menu views and engagement.
"""
from django.db import models

from apps.core.managers import TenantManager
from apps.core.models import TenantModel


class MenuView(TenantModel):
    """
    Individual menu view event.

    Tracks when a customer views a restaurant's public menu.
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
            models.Index(fields=["restaurant", "viewed_at"]),
            models.Index(fields=["restaurant", "session_id"]),
        ]

    def __str__(self):
        return f"Menu view for {self.restaurant} at {self.viewed_at}"


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
        unique_together = [("restaurant", "date")]
        verbose_name_plural = "Daily menu stats"
        indexes = [
            models.Index(fields=["restaurant", "date"]),
        ]

    def __str__(self):
        return f"Stats for {self.restaurant} on {self.date}"
