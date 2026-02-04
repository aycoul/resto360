"""
Invoicing models for BIZ360 - DGI Electronic Invoice Compliance.

Supports Ivory Coast DGI electronic invoicing requirements:
- FNE (Facture Normalisée Électronique): Standardized electronic invoice
- RNE (Registre Numérique des Encaissements): Digital receipts register

References:
- DGI Ivory Coast: https://www.dgi.gouv.ci
- Mandate: Businesses with turnover > 50M XOF must comply
"""

from django.db import models

from apps.core.managers import TenantManager
from apps.core.models import BaseModel, TenantModel


class DGIConfiguration(BaseModel):
    """Business DGI integration settings."""

    business = models.OneToOneField(
        "authentication.Business",
        on_delete=models.CASCADE,
        related_name="dgi_config",
    )

    # DGI credentials
    taxpayer_id = models.CharField(
        max_length=50,
        help_text="NCC (Numéro de Compte Contribuable)",
    )
    establishment_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Establishment identifier (if multiple locations)",
    )
    api_key = models.CharField(
        max_length=255,
        help_text="DGI API key (should be encrypted in production)",
    )
    api_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="DGI API secret (should be encrypted in production)",
    )

    # Environment
    is_production = models.BooleanField(
        default=False,
        help_text="Use production API (vs sandbox for testing)",
    )

    # Status
    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    class Meta:
        verbose_name = "DGI Configuration"
        verbose_name_plural = "DGI Configurations"

    def __str__(self):
        return f"DGI Config - {self.business.name}"


class ElectronicInvoiceStatus(models.TextChoices):
    """Electronic invoice status enumeration."""

    DRAFT = "draft", "Draft"
    PENDING_VALIDATION = "pending_validation", "Pending Validation"
    VALIDATED = "validated", "Validated"
    REJECTED = "rejected", "Rejected"
    CANCELLED = "cancelled", "Cancelled"


class ElectronicInvoice(TenantModel):
    """DGI-compliant electronic invoice."""

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="electronic_invoice",
    )

    # Invoice identification
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateTimeField()

    # DGI fields (populated after validation)
    dgi_uid = models.CharField(
        max_length=100,
        blank=True,
        help_text="DGI unique identifier",
    )
    dgi_qr_code = models.TextField(
        blank=True,
        help_text="QR code data for verification",
    )
    dgi_signature = models.TextField(
        blank=True,
        help_text="Digital signature from DGI",
    )
    dgi_validation_date = models.DateTimeField(null=True, blank=True)

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=ElectronicInvoiceStatus.choices,
        default=ElectronicInvoiceStatus.DRAFT,
    )
    rejection_reason = models.TextField(blank=True)

    # Amounts (in XOF)
    subtotal_ht = models.PositiveIntegerField(
        help_text="Subtotal Hors Taxe (excluding tax)",
    )
    tva_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
        help_text="TVA rate (default 18%)",
    )
    tva_amount = models.PositiveIntegerField(
        help_text="TVA (tax) amount",
    )
    total_ttc = models.PositiveIntegerField(
        help_text="Total TTC (including tax)",
    )
    discount_amount = models.PositiveIntegerField(
        default=0,
        help_text="Discount amount",
    )

    # Seller information (copied from business for historical accuracy)
    seller_name = models.CharField(max_length=255)
    seller_ncc = models.CharField(
        max_length=50,
        help_text="Seller's NCC (tax ID)",
    )
    seller_address = models.TextField()
    seller_phone = models.CharField(max_length=20, blank=True)
    seller_email = models.EmailField(blank=True)

    # Customer information
    customer_name = models.CharField(max_length=255)
    customer_ncc = models.CharField(
        max_length=50,
        blank=True,
        help_text="Customer's NCC for B2B invoices",
    )
    customer_address = models.TextField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)

    # PDF storage
    pdf_file = models.FileField(
        upload_to="invoices/",
        blank=True,
        help_text="Generated PDF invoice",
    )

    # API response storage (for debugging)
    api_request = models.JSONField(default=dict, blank=True)
    api_response = models.JSONField(default=dict, blank=True)

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-invoice_date"]
        verbose_name = "Electronic Invoice"
        verbose_name_plural = "Electronic Invoices"
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["dgi_uid"]),
        ]

    def __str__(self):
        return f"Invoice {self.invoice_number}"


class ElectronicInvoiceLine(TenantModel):
    """Line item in an electronic invoice."""

    invoice = models.ForeignKey(
        ElectronicInvoice,
        on_delete=models.CASCADE,
        related_name="lines",
    )

    # Item details
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price_ht = models.PositiveIntegerField(
        help_text="Unit price HT (excluding tax)",
    )
    unit_price_ttc = models.PositiveIntegerField(
        help_text="Unit price TTC (including tax)",
    )

    # Tax
    tva_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
    )
    tva_amount = models.PositiveIntegerField()

    # Totals
    line_total_ht = models.PositiveIntegerField()
    line_total_ttc = models.PositiveIntegerField()

    # Reference to original order item
    order_item = models.ForeignKey(
        "orders.OrderItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Use standard manager for related lookups
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.quantity}x {self.description}"
