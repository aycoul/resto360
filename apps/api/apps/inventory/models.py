from decimal import Decimal

from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.managers import TenantManager
from apps.core.models import TenantModel


class UnitType(models.TextChoices):
    """Units of measurement for stock items."""

    KG = "kg", "Kilogram"
    G = "g", "Gram"
    L = "L", "Litre"
    ML = "mL", "Millilitre"
    PIECE = "piece", "Piece"
    PORTION = "portion", "Portion"
    OTHER = "other", "Other"


class MovementType(models.TextChoices):
    """Types of stock movements."""

    IN = "in", "Stock In"
    OUT = "out", "Stock Out"
    ADJUSTMENT = "adjustment", "Adjustment"


class MovementReason(models.TextChoices):
    """Reasons for stock movements."""

    PURCHASE = "purchase", "Purchase"
    ORDER_USAGE = "order_usage", "Order Usage"
    WASTE = "waste", "Waste"
    THEFT = "theft", "Theft"
    CORRECTION = "correction", "Correction"
    TRANSFER = "transfer", "Transfer"
    INITIAL = "initial", "Initial Stock"


class StockItem(TenantModel):
    """A stock item tracked in inventory."""

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, blank=True, help_text="Optional SKU code")
    unit = models.CharField(
        max_length=20, choices=UnitType.choices, default=UnitType.PIECE
    )
    current_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0"),
        help_text="Current quantity in stock",
    )
    low_stock_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Alert when stock falls below this level",
    )
    low_stock_alert_sent = models.BooleanField(
        default=False, help_text="Prevents duplicate alerts"
    )
    is_active = models.BooleanField(default=True)

    # django-simple-history for audit trail
    history = HistoricalRecords()

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(current_quantity__gte=0),
                name="stock_item_non_negative_quantity",
            ),
            models.UniqueConstraint(
                fields=["business", "sku"],
                condition=~models.Q(sku=""),
                name="unique_business_sku",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.current_quantity} {self.unit})"

    @property
    def is_low_stock(self):
        """Check if current quantity is at or below threshold."""
        if self.low_stock_threshold is None:
            return False
        return self.current_quantity <= self.low_stock_threshold


class StockMovement(TenantModel):
    """An immutable record of a stock movement."""

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name="movements",
    )
    quantity_change = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Positive for stock in, negative for stock out",
    )
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    reason = models.CharField(max_length=20, choices=MovementReason.choices)
    notes = models.TextField(blank=True)
    reference_type = models.CharField(
        max_length=50, blank=True, help_text="Type of reference (e.g., 'Order')"
    )
    reference_id = models.UUIDField(null=True, blank=True, help_text="Reference object ID")
    balance_after = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Stock balance after this movement",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="stock_movements",
    )

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["stock_item", "-created_at"]),
            models.Index(fields=["business", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.stock_item.name}: {self.quantity_change:+} ({self.reason})"

    def save(self, *args, **kwargs):
        """Prevent updates to existing movements (immutable records)."""
        if self.pk is not None:
            # Check if this is an existing record being updated
            existing = StockMovement.all_objects.filter(pk=self.pk).exists()
            if existing:
                raise ValueError("StockMovement records are immutable and cannot be updated.")
        super().save(*args, **kwargs)


class MenuItemIngredient(TenantModel):
    """Maps a menu item to its required ingredients (recipe/BOM)."""

    menu_item = models.ForeignKey(
        "menu.Product",
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",  # product.recipe_ingredients.all()
    )
    stock_item = models.ForeignKey(
        "inventory.StockItem",
        on_delete=models.CASCADE,
        related_name="menu_usages",  # stockitem.menu_usages.all()
    )
    quantity_required = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Quantity of this ingredient required per 1 unit of menu item",
    )

    # Standard managers
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        unique_together = ["menu_item", "stock_item"]
        ordering = ["stock_item__name"]

    def __str__(self):
        return f"{self.menu_item.name}: {self.quantity_required} {self.stock_item.unit} of {self.stock_item.name}"
