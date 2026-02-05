"""
Models for the Supplier Marketplace.

This module provides models for managing suppliers, their products,
orders between businesss and suppliers, and supplier reviews.
"""

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class Supplier(BaseModel):
    """
    Represents a supplier in the marketplace.

    Suppliers can register to sell products to businesss.
    They must be verified before their products become visible.
    """

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending Review"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"

    class SupplierType(models.TextChoices):
        PRODUCER = "producer", "Producer/Farmer"
        WHOLESALER = "wholesaler", "Wholesaler"
        DISTRIBUTOR = "distributor", "Distributor"
        MANUFACTURER = "manufacturer", "Manufacturer"
        IMPORTER = "importer", "Importer"

    # Basic Info
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    supplier_type = models.CharField(
        max_length=20,
        choices=SupplierType.choices,
        default=SupplierType.WHOLESALER,
    )

    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)

    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="Senegal")
    postal_code = models.CharField(max_length=20, blank=True)

    # Branding
    logo = models.ImageField(upload_to="suppliers/logos/", blank=True, null=True)
    cover_image = models.ImageField(upload_to="suppliers/covers/", blank=True, null=True)

    # Verification
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verified_at = models.DateTimeField(blank=True, null=True)
    verification_notes = models.TextField(blank=True)

    # Business details
    business_registration = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    years_in_business = models.PositiveSmallIntegerField(default=0)

    # Delivery
    minimum_order_value = models.DecimalField(
        max_digits=10, decimal_places=0, default=0,
        help_text="Minimum order value in XOF"
    )
    delivery_areas = models.JSONField(
        default=list, blank=True,
        help_text="List of cities/regions the supplier delivers to"
    )
    delivery_days = models.JSONField(
        default=list, blank=True,
        help_text="Days of the week for delivery (0=Monday, 6=Sunday)"
    )
    lead_time_days = models.PositiveSmallIntegerField(
        default=1,
        help_text="Number of days advance notice required for orders"
    )

    # Payment
    accepted_payment_methods = models.JSONField(
        default=list, blank=True,
        help_text="List of accepted payment methods"
    )
    payment_terms = models.CharField(
        max_length=50, blank=True,
        help_text="e.g., 'Net 30', 'COD', 'Prepaid'"
    )

    # Stats (denormalized for performance)
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)

    # Owner (the user who manages this supplier account)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="owned_suppliers",
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_featured", "-average_rating", "name"]
        indexes = [
            models.Index(fields=["verification_status", "is_active"]),
            models.Index(fields=["city", "is_active"]),
            models.Index(fields=["average_rating"]),
        ]

    def __str__(self):
        return self.name

    @property
    def is_verified(self):
        return self.verification_status == self.VerificationStatus.VERIFIED


class SupplierCategory(BaseModel):
    """
    Categories for organizing supplier products.

    Examples: Produce, Meat & Poultry, Seafood, Dairy, Beverages, Packaging, etc.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name or emoji")
    image = models.ImageField(upload_to="marketplace/categories/", blank=True, null=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Supplier categories"
        ordering = ["display_order", "name"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class SupplierProduct(BaseModel):
    """
    Products offered by suppliers.

    Each product belongs to a supplier and one or more categories.
    """

    class Unit(models.TextChoices):
        PIECE = "piece", "Piece"
        KG = "kg", "Kilogram"
        G = "g", "Gram"
        L = "l", "Liter"
        ML = "ml", "Milliliter"
        BOX = "box", "Box"
        CASE = "case", "Case"
        PACK = "pack", "Pack"
        DOZEN = "dozen", "Dozen"
        PALLET = "pallet", "Pallet"

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="products",
    )
    category = models.ForeignKey(
        SupplierCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="products",
    )

    # Basic Info
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=50, blank=True, help_text="Supplier's SKU")

    # Pricing
    unit = models.CharField(max_length=20, choices=Unit.choices, default=Unit.KG)
    unit_size = models.DecimalField(
        max_digits=10, decimal_places=2, default=1,
        help_text="Size per unit (e.g., 25 for a 25kg bag)"
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=0,
        help_text="Price per unit in XOF"
    )

    # Bulk pricing tiers
    bulk_pricing = models.JSONField(
        default=list, blank=True,
        help_text="List of {min_quantity, price} objects for bulk discounts"
    )

    # Ordering constraints
    minimum_order_quantity = models.PositiveIntegerField(
        default=1,
        help_text="Minimum quantity per order"
    )
    order_increment = models.PositiveIntegerField(
        default=1,
        help_text="Quantity must be ordered in multiples of this"
    )

    # Availability
    is_available = models.BooleanField(default=True)
    stock_status = models.CharField(
        max_length=20,
        choices=[
            ("in_stock", "In Stock"),
            ("low_stock", "Low Stock"),
            ("out_of_stock", "Out of Stock"),
            ("made_to_order", "Made to Order"),
        ],
        default="in_stock",
    )
    lead_time_days = models.PositiveSmallIntegerField(
        default=0,
        help_text="Additional lead time for this product (beyond supplier default)"
    )

    # Media
    image = models.ImageField(upload_to="marketplace/products/", blank=True, null=True)
    images = models.JSONField(
        default=list, blank=True,
        help_text="Additional product images"
    )

    # Attributes
    origin = models.CharField(max_length=100, blank=True, help_text="Country/region of origin")
    brand = models.CharField(max_length=100, blank=True)
    certifications = models.JSONField(
        default=list, blank=True,
        help_text="e.g., ['Organic', 'Halal', 'Fair Trade']"
    )

    # Stats
    times_ordered = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["name"]
        unique_together = [["supplier", "slug"]]
        indexes = [
            models.Index(fields=["supplier", "is_available"]),
            models.Index(fields=["category", "is_available"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.supplier.name})"

    def get_price_for_quantity(self, quantity: int) -> Decimal:
        """Get the unit price for a given quantity, applying bulk discounts."""
        if not self.bulk_pricing:
            return self.price

        applicable_price = self.price
        for tier in sorted(self.bulk_pricing, key=lambda x: x.get("min_quantity", 0)):
            if quantity >= tier.get("min_quantity", 0):
                applicable_price = Decimal(str(tier.get("price", self.price)))

        return applicable_price


class SupplierOrder(BaseModel):
    """
    An order placed by a business to a supplier.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PARTIAL = "partial", "Partially Paid"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"

    # Order number
    order_number = models.CharField(max_length=50, unique=True)

    # Parties
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    business = models.ForeignKey(
        "authentication.Business",
        on_delete=models.PROTECT,
        related_name="supplier_orders",
    )
    placed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="placed_supplier_orders",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    # Dates
    submitted_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    expected_delivery = models.DateField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    # Delivery
    delivery_address = models.TextField()
    delivery_instructions = models.TextField(blank=True)

    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    # Payment
    amount_paid = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)

    # Notes
    business_notes = models.TextField(blank=True, help_text="Notes from business to supplier")
    supplier_notes = models.TextField(blank=True, help_text="Notes from supplier")
    internal_notes = models.TextField(blank=True, help_text="Internal notes (not visible to other party)")

    # Invoice
    invoice_number = models.CharField(max_length=50, blank=True)
    invoice_file = models.FileField(upload_to="marketplace/invoices/", blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["supplier", "status"]),
            models.Index(fields=["order_number"]),
            models.Index(fields=["expected_delivery"]),
        ]

    def __str__(self):
        return f"Order {self.order_number} - {self.business.name} to {self.supplier.name}"

    def calculate_totals(self):
        """Recalculate order totals from items."""
        self.subtotal = sum(item.line_total for item in self.items.all())
        self.total = self.subtotal + self.delivery_fee + self.tax - self.discount

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: SO-YYYYMMDD-XXXX
            today = timezone.now().strftime("%Y%m%d")
            count = SupplierOrder.objects.filter(
                order_number__startswith=f"SO-{today}"
            ).count()
            self.order_number = f"SO-{today}-{count + 1:04d}"
        super().save(*args, **kwargs)


class SupplierOrderItem(BaseModel):
    """
    Individual line items in a supplier order.
    """

    order = models.ForeignKey(
        SupplierOrder,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        SupplierProduct,
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    # Snapshot of product details at time of order
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50, blank=True)
    unit = models.CharField(max_length=20)
    unit_size = models.DecimalField(max_digits=10, decimal_places=2)

    # Quantities
    quantity = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)

    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=0)

    # Notes
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    def save(self, *args, **kwargs):
        # Calculate line total
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class SupplierReview(BaseModel):
    """
    Reviews of suppliers by businesss.
    """

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    business = models.ForeignKey(
        "authentication.Business",
        on_delete=models.CASCADE,
        related_name="supplier_reviews",
    )
    order = models.ForeignKey(
        SupplierOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="supplier_reviews",
    )

    # Ratings (1-5)
    overall_rating = models.PositiveSmallIntegerField()
    quality_rating = models.PositiveSmallIntegerField(blank=True, null=True)
    delivery_rating = models.PositiveSmallIntegerField(blank=True, null=True)
    communication_rating = models.PositiveSmallIntegerField(blank=True, null=True)
    value_rating = models.PositiveSmallIntegerField(blank=True, null=True)

    # Content
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()

    # Response
    supplier_response = models.TextField(blank=True)
    response_at = models.DateTimeField(blank=True, null=True)

    # Moderation
    is_verified = models.BooleanField(default=False, help_text="Verified purchase")
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["supplier", "business", "order"]]
        indexes = [
            models.Index(fields=["supplier", "is_published"]),
            models.Index(fields=["overall_rating"]),
        ]

    def __str__(self):
        return f"Review of {self.supplier.name} by {self.business.name}"


class SupplierFavorite(BaseModel):
    """
    Restaurants can save suppliers as favorites for quick access.
    """

    business = models.ForeignKey(
        "authentication.Business",
        on_delete=models.CASCADE,
        related_name="favorite_suppliers",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    notes = models.TextField(blank=True, help_text="Private notes about this supplier")

    class Meta:
        unique_together = [["business", "supplier"]]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.business.name} -> {self.supplier.name}"


class Cart(BaseModel):
    """
    Shopping cart for a business ordering from suppliers.

    Each business can have one active cart per supplier.
    """

    business = models.ForeignKey(
        "authentication.Business",
        on_delete=models.CASCADE,
        related_name="supplier_carts",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="carts",
    )

    class Meta:
        unique_together = [["business", "supplier"]]

    def __str__(self):
        return f"Cart: {self.business.name} <- {self.supplier.name}"

    @property
    def total(self) -> Decimal:
        return sum(item.line_total for item in self.items.all())

    @property
    def item_count(self) -> int:
        return self.items.count()


class CartItem(BaseModel):
    """
    Items in a shopping cart.
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        SupplierProduct,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [["cart", "product"]]

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def unit_price(self) -> Decimal:
        return self.product.get_price_for_quantity(self.quantity)

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity
