"""Order models for RESTO360."""

from django.db import models, transaction
from django.utils import timezone

from apps.core.managers import TenantManager
from apps.core.models import BaseModel, TenantModel


class OrderType(models.TextChoices):
    """Order type enumeration."""

    DINE_IN = "dine_in", "Dine In"
    TAKEAWAY = "takeaway", "Takeaway"
    DELIVERY = "delivery", "Delivery"


class OrderStatus(models.TextChoices):
    """Order status enumeration."""

    PENDING = "pending", "Pending"
    PREPARING = "preparing", "Preparing"
    READY = "ready", "Ready"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Table(TenantModel):
    """Restaurant table for dine-in orders."""

    number = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField(default=4)
    is_active = models.BooleanField(default=True)

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["number"]
        unique_together = [["restaurant", "number"]]

    def __str__(self):
        return f"Table {self.number}"


class DailySequence(BaseModel):
    """
    Track daily order sequence numbers per restaurant.

    Each restaurant gets a new sequence each day, starting at 1.
    """

    restaurant = models.ForeignKey(
        "authentication.Restaurant",
        on_delete=models.CASCADE,
        related_name="daily_sequences",
    )
    date = models.DateField()
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [["restaurant", "date"]]

    def __str__(self):
        return f"{self.restaurant.name} - {self.date}: {self.last_number}"


class Order(TenantModel):
    """
    Customer order with items and modifiers.

    Orders are assigned a unique daily number per restaurant.
    """

    order_number = models.PositiveIntegerField(
        help_text="Daily order number (resets each day per restaurant)"
    )
    order_date = models.DateField(
        help_text="Date of the order (for daily sequence uniqueness)",
        null=True,  # Allow null for migration, will be auto-set
    )
    order_type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.DINE_IN,
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Required for dine-in orders",
    )
    cashier = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders_created",
    )
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    subtotal = models.PositiveIntegerField(
        default=0,
        help_text="Subtotal in XOF before any discounts",
    )
    discount = models.PositiveIntegerField(
        default=0,
        help_text="Discount amount in XOF",
    )
    total = models.PositiveIntegerField(
        default=0,
        help_text="Final total in XOF (subtotal - discount)",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_reason = models.TextField(blank=True)

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["restaurant", "order_number", "order_date"]]
        indexes = [
            models.Index(fields=["restaurant", "status"]),
            models.Index(fields=["restaurant", "created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Order #{self.order_number}"

    def calculate_totals(self):
        """Recalculate subtotal and total from items."""
        self.subtotal = sum(item.line_total for item in self.items.all())
        self.total = max(0, self.subtotal - self.discount)

    def save(self, *args, **kwargs):
        """Auto-set timestamps based on status changes."""
        # Auto-set order_date for daily sequence uniqueness
        if not self.order_date:
            self.order_date = timezone.now().date()
        if self.status == OrderStatus.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        if self.status == OrderStatus.CANCELLED and not self.cancelled_at:
            self.cancelled_at = timezone.now()
        super().save(*args, **kwargs)


class OrderItem(TenantModel):
    """Line item in an order."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    menu_item = models.ForeignKey(
        "menu.MenuItem",
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_items",
    )
    name = models.CharField(
        max_length=200,
        help_text="Copied from menu item at order time for historical accuracy",
    )
    unit_price = models.PositiveIntegerField(
        help_text="Price in XOF at order time",
    )
    quantity = models.PositiveIntegerField(default=1)
    modifiers_total = models.IntegerField(
        default=0,
        help_text="Sum of modifier price adjustments (can be negative)",
    )
    line_total = models.PositiveIntegerField(
        default=0,
        help_text="(unit_price + modifiers_total) * quantity",
    )
    notes = models.TextField(blank=True)

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.quantity}x {self.name}"

    def calculate_line_total(self):
        """Calculate line total from price, modifiers, and quantity."""
        self.modifiers_total = sum(
            mod.price_adjustment for mod in self.modifiers.all()
        )
        self.line_total = max(0, (self.unit_price + self.modifiers_total) * self.quantity)

    def save(self, *args, **kwargs):
        """Auto-calculate line total before saving."""
        # If this is an existing item, recalculate
        if self.pk:
            self.calculate_line_total()
        else:
            # For new items, just set basic line total without modifiers
            self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderItemModifier(TenantModel):
    """Modifier applied to an order item."""

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="modifiers",
    )
    modifier_option = models.ForeignKey(
        "menu.ModifierOption",
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_item_modifiers",
    )
    name = models.CharField(
        max_length=100,
        help_text="Copied from modifier option at order time",
    )
    price_adjustment = models.IntegerField(
        default=0,
        help_text="Price adjustment in XOF (can be negative)",
    )

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.name
