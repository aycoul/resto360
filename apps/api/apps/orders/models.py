"""Order models for BIZ360 (formerly RESTO360)."""

from django.db import models, transaction
from django.utils import timezone

from apps.core.managers import TenantManager
from apps.core.models import BaseModel, TenantModel


class OrderType(models.TextChoices):
    """Order type enumeration."""

    DINE_IN = "dine_in", "Dine In"
    TAKEAWAY = "takeaway", "Takeaway"
    DELIVERY = "delivery", "Delivery"
    # New types for non-restaurant businesses
    IN_STORE = "in_store", "In Store"
    ONLINE = "online", "Online"


class OrderStatus(models.TextChoices):
    """Order status enumeration."""

    PENDING = "pending", "Pending"
    PREPARING = "preparing", "Preparing"
    READY = "ready", "Ready"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class DGISubmissionStatus(models.TextChoices):
    """DGI electronic invoice submission status."""

    NOT_REQUIRED = "not_required", "Not Required"
    PENDING = "pending", "Pending"
    SUBMITTED = "submitted", "Submitted"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"


class Table(TenantModel):
    """Business table for dine-in orders (restaurants, cafes)."""

    number = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField(default=4)
    is_active = models.BooleanField(default=True)

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["number"]
        unique_together = [["business", "number"]]

    def __str__(self):
        return f"Table {self.number}"


class DailySequence(BaseModel):
    """
    Track daily order sequence numbers per business.

    Each business gets a new sequence each day, starting at 1.
    Used for quick daily order reference (Order #1, #2, etc.)
    """

    business = models.ForeignKey(
        "authentication.Business",
        on_delete=models.CASCADE,
        related_name="daily_sequences",
    )
    date = models.DateField()
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [["business", "date"]]

    def __str__(self):
        return f"{self.business.name} - {self.date}: {self.last_number}"


class InvoiceSequence(BaseModel):
    """
    Track sequential invoice numbers per business (never resets).

    Used for DGI-compliant invoice numbering.
    Format: BIZ-{business_id}-{year}-{sequence}
    """

    business = models.ForeignKey(
        "authentication.Business",
        on_delete=models.CASCADE,
        related_name="invoice_sequences",
    )
    year = models.PositiveIntegerField()
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [["business", "year"]]

    def __str__(self):
        return f"{self.business.name} - {self.year}: {self.last_number}"


class Order(TenantModel):
    """
    Customer order with items and modifiers.

    Orders are assigned:
    - A daily order number (resets each day) for quick reference
    - A sequential invoice number (never resets) for DGI compliance
    """

    # Daily order number (for quick reference, resets daily)
    order_number = models.PositiveIntegerField(
        help_text="Daily order number (resets each day per business)"
    )
    order_date = models.DateField(
        help_text="Date of the order (for daily sequence uniqueness)",
        null=True,  # Allow null for migration, will be auto-set
    )

    # Invoice number (sequential, never resets - for DGI compliance)
    invoice_number = models.CharField(
        max_length=50,
        blank=True,
        unique=True,
        null=True,  # Null until invoice is generated
        help_text="Sequential invoice number (BIZ-XXX-YYYY-NNNNNN)",
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

    # Customer information
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_tax_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Customer's NCC for B2B invoices",
    )
    customer_address = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    # Pricing (subtotal is before tax if prices are tax-exclusive)
    subtotal = models.PositiveIntegerField(
        default=0,
        help_text="Subtotal in XOF before discounts and tax",
    )
    discount = models.PositiveIntegerField(
        default=0,
        help_text="Discount amount in XOF",
    )

    # Tax fields (NEW)
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
        help_text="Tax rate applied (default: Ivory Coast VAT 18%)",
    )
    tax_amount = models.PositiveIntegerField(
        default=0,
        help_text="Total tax amount in XOF",
    )
    subtotal_ht = models.PositiveIntegerField(
        default=0,
        help_text="Subtotal Hors Taxe (excluding tax) in XOF",
    )

    total = models.PositiveIntegerField(
        default=0,
        help_text="Final total in XOF (TTC - including tax)",
    )

    # DGI electronic invoice compliance (NEW)
    dgi_submission_status = models.CharField(
        max_length=20,
        choices=DGISubmissionStatus.choices,
        default=DGISubmissionStatus.NOT_REQUIRED,
    )
    dgi_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="DGI unique identifier after submission",
    )
    dgi_submitted_at = models.DateTimeField(null=True, blank=True)
    dgi_qr_code = models.TextField(
        blank=True,
        help_text="QR code data for DGI verification",
    )

    # Timestamps
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_reason = models.TextField(blank=True)

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["business", "order_number", "order_date"]]
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["business", "created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["dgi_submission_status"]),
        ]

    def __str__(self):
        return f"Order #{self.order_number}"

    def calculate_totals(self):
        """Recalculate subtotal, tax, and total from items."""
        from decimal import Decimal

        items_total = sum(item.line_total for item in self.items.all())
        self.subtotal = items_total

        # Calculate tax (assuming prices are tax-inclusive by default)
        if self.business.default_tax_rate > 0:
            tax_rate = Decimal(str(self.tax_rate))
            tax_divisor = 1 + (tax_rate / Decimal("100"))
            self.subtotal_ht = int(Decimal(items_total) / tax_divisor)
            self.tax_amount = items_total - self.subtotal_ht
        else:
            self.subtotal_ht = items_total
            self.tax_amount = 0

        self.total = max(0, self.subtotal - self.discount)

    def generate_invoice_number(self):
        """Generate sequential invoice number (never resets)."""
        if self.invoice_number:
            return self.invoice_number

        year = timezone.now().year
        prefix = f"BIZ-{self.business.id.hex[:6].upper()}-{year}"

        # Get or create sequence for this business/year
        sequence, _ = InvoiceSequence.objects.get_or_create(
            business=self.business,
            year=year,
            defaults={"last_number": 0}
        )

        # Atomically increment the sequence
        with transaction.atomic():
            sequence = InvoiceSequence.objects.select_for_update().get(
                pk=sequence.pk
            )
            sequence.last_number += 1
            sequence.save()

        self.invoice_number = f"{prefix}-{sequence.last_number:06d}"
        return self.invoice_number

    def save(self, *args, **kwargs):
        """Auto-set timestamps based on status changes."""
        # Auto-set order_date for daily sequence uniqueness
        if not self.order_date:
            self.order_date = timezone.now().date()

        # Auto-set tax rate from business if not set
        if not self.pk and self.business:
            self.tax_rate = self.business.default_tax_rate

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
        "menu.Product",
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
        # For existing items (update), recalculate based on saved modifiers
        # Use _state.adding because UUID pks are set before save
        if not self._state.adding:
            self.calculate_line_total()
        # For new items, only calculate if line_total wasn't already set
        # This allows serializers to pass pre-calculated values
        elif self.line_total == 0:
            self.line_total = (self.unit_price + self.modifiers_total) * self.quantity
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
