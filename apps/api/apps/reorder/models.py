"""
Reorder models for BIZ360.

Supports two reorder flows:
1. QR Package Reorder: Customer scans QR on product packaging to quickly reorder
2. Order History Reorder: Customer views past orders and reorders previous items
"""

import uuid

from django.db import models

from apps.core.managers import TenantManager
from apps.core.models import BaseModel, TenantModel


class ReorderQRCode(TenantModel):
    """QR code for product reordering from packaging."""

    product = models.ForeignKey(
        "menu.Product",
        on_delete=models.CASCADE,
        related_name="reorder_qr_codes",
    )

    # QR Code unique identifier
    code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Unique code embedded in QR",
    )

    # Reorder settings
    default_quantity = models.PositiveIntegerField(
        default=1,
        help_text="Default quantity when scanning QR",
    )
    min_quantity = models.PositiveIntegerField(
        default=1,
        help_text="Minimum order quantity",
    )
    max_quantity = models.PositiveIntegerField(
        default=100,
        help_text="Maximum order quantity",
    )

    # Customer info settings
    require_name = models.BooleanField(
        default=True,
        help_text="Require customer name",
    )
    require_phone = models.BooleanField(
        default=True,
        help_text="Require customer phone",
    )
    require_address = models.BooleanField(
        default=False,
        help_text="Require delivery address",
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Stats
    scan_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of scans",
    )
    order_count = models.PositiveIntegerField(
        default=0,
        help_text="Total orders placed via this QR",
    )

    # Custom message/promotion
    promo_message = models.TextField(
        blank=True,
        help_text="Optional promotional message shown on reorder page",
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Discount percentage for QR orders",
    )

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Reorder QR Code"
        verbose_name_plural = "Reorder QR Codes"

    def __str__(self):
        return f"QR: {self.product.name} ({self.code})"

    def increment_scan(self):
        """Increment scan count."""
        self.scan_count += 1
        self.save(update_fields=["scan_count", "updated_at"])

    def increment_order(self):
        """Increment order count."""
        self.order_count += 1
        self.save(update_fields=["order_count", "updated_at"])


class ReorderScan(TenantModel):
    """Track QR code scans for analytics."""

    qr_code = models.ForeignKey(
        ReorderQRCode,
        on_delete=models.CASCADE,
        related_name="scans",
    )

    # Scan info
    scanned_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)

    # Conversion tracking
    converted_to_order = models.BooleanField(default=False)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reorder_scans",
    )
    converted_at = models.DateTimeField(null=True, blank=True)

    # Session tracking
    session_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Browser session ID for tracking",
    )

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-scanned_at"]

    def __str__(self):
        return f"Scan: {self.qr_code.product.name} @ {self.scanned_at}"


class CustomerProfile(BaseModel):
    """
    Customer profile for order history tracking.

    Allows customers to view their past orders and reorder.
    """

    phone = models.CharField(
        max_length=20,
        unique=True,
        help_text="Primary identifier for customer",
    )
    email = models.EmailField(blank=True)
    name = models.CharField(max_length=255, blank=True)

    # Default delivery address
    default_address = models.TextField(blank=True)

    # Verification
    is_verified = models.BooleanField(
        default=False,
        help_text="Phone number verified via SMS",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    # Marketing
    accepts_marketing = models.BooleanField(default=False)

    # Stats
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.PositiveIntegerField(default=0)
    last_order_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer Profiles"

    def __str__(self):
        return f"{self.name or 'Customer'} ({self.phone})"

    def update_stats(self, order):
        """Update stats after an order is placed."""
        self.total_orders += 1
        self.total_spent += order.total
        self.last_order_at = order.created_at
        self.save(update_fields=[
            "total_orders", "total_spent", "last_order_at", "updated_at"
        ])


class OrderHistory(TenantModel):
    """
    Link orders to customer profiles for reorder capability.

    Enables customers to view past orders with any business and reorder.
    """

    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name="order_history",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="customer_history",
    )

    # Quick access fields (denormalized for performance)
    order_total = models.PositiveIntegerField()
    order_date = models.DateTimeField()
    item_count = models.PositiveIntegerField()

    # Reorder stats
    reorder_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this order was reordered",
    )
    last_reordered_at = models.DateTimeField(null=True, blank=True)

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-order_date"]
        unique_together = ["customer", "order"]
        verbose_name = "Order History"
        verbose_name_plural = "Order Histories"

    def __str__(self):
        return f"{self.customer.phone} - Order #{self.order.order_number}"

    def increment_reorder(self):
        """Track when this order is reordered."""
        from django.utils import timezone
        self.reorder_count += 1
        self.last_reordered_at = timezone.now()
        self.save(update_fields=["reorder_count", "last_reordered_at", "updated_at"])
