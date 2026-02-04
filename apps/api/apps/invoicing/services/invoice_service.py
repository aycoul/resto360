"""
Invoice Service for BIZ360.

Handles invoice generation, PDF creation, and DGI submission orchestration.
"""

import logging
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order

from ..models import (
    DGIConfiguration,
    ElectronicInvoice,
    ElectronicInvoiceLine,
    ElectronicInvoiceStatus,
)
from .dgi_service import DGIService, DGIError

logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for invoice generation and management."""

    def __init__(self, business):
        """
        Initialize invoice service for a business.

        Args:
            business: Business instance
        """
        self.business = business

    def create_invoice_from_order(self, order: Order) -> ElectronicInvoice:
        """
        Create electronic invoice from an order.

        Args:
            order: Order instance

        Returns:
            ElectronicInvoice: Created invoice
        """
        # Ensure order has an invoice number
        if not order.invoice_number:
            order.generate_invoice_number()
            order.save(update_fields=["invoice_number", "updated_at"])

        with transaction.atomic():
            # Create the invoice
            invoice = ElectronicInvoice.objects.create(
                business=self.business,
                order=order,
                invoice_number=order.invoice_number,
                invoice_date=timezone.now(),
                status=ElectronicInvoiceStatus.DRAFT,
                # Amounts
                subtotal_ht=order.subtotal_ht,
                tva_rate=order.tax_rate,
                tva_amount=order.tax_amount,
                total_ttc=order.total,
                discount_amount=order.discount,
                # Seller info
                seller_name=self.business.name,
                seller_ncc=self.business.tax_id,
                seller_address=self.business.address,
                seller_phone=self.business.phone,
                seller_email=self.business.email,
                # Customer info
                customer_name=order.customer_name or "Client Anonyme",
                customer_ncc=order.customer_tax_id,
                customer_address=order.customer_address,
                customer_phone=order.customer_phone,
                customer_email=order.customer_email,
            )

            # Create invoice lines from order items
            for item in order.items.all():
                self._create_invoice_line(invoice, item)

            return invoice

    def _create_invoice_line(
        self,
        invoice: ElectronicInvoice,
        order_item
    ) -> ElectronicInvoiceLine:
        """
        Create invoice line from order item.

        Args:
            invoice: Parent invoice
            order_item: OrderItem instance

        Returns:
            ElectronicInvoiceLine: Created line
        """
        # Calculate HT price from TTC (assuming prices are tax-inclusive)
        ttc_price = order_item.unit_price + order_item.modifiers_total
        tax_rate = invoice.tva_rate
        tax_divisor = 1 + (tax_rate / Decimal("100"))
        ht_price = int(Decimal(ttc_price) / tax_divisor)
        tva_per_unit = ttc_price - ht_price

        line_total_ht = ht_price * order_item.quantity
        line_total_ttc = ttc_price * order_item.quantity
        tva_amount = tva_per_unit * order_item.quantity

        return ElectronicInvoiceLine.objects.create(
            business=self.business,
            invoice=invoice,
            order_item=order_item,
            description=order_item.name,
            quantity=order_item.quantity,
            unit_price_ht=ht_price,
            unit_price_ttc=ttc_price,
            tva_rate=tax_rate,
            tva_amount=tva_amount,
            line_total_ht=line_total_ht,
            line_total_ttc=line_total_ttc,
        )

    def submit_to_dgi(self, invoice: ElectronicInvoice) -> bool:
        """
        Submit invoice to DGI for validation.

        Args:
            invoice: ElectronicInvoice to submit

        Returns:
            bool: True if submission successful
        """
        # Check if DGI is configured
        try:
            config = DGIConfiguration.objects.get(business=self.business)
        except DGIConfiguration.DoesNotExist:
            logger.warning(f"DGI not configured for business {self.business.id}")
            return False

        if not config.is_active:
            logger.warning(f"DGI configuration inactive for business {self.business.id}")
            return False

        # Update status to pending
        invoice.status = ElectronicInvoiceStatus.PENDING_VALIDATION
        invoice.save(update_fields=["status", "updated_at"])

        # Submit to DGI
        service = DGIService(config)
        try:
            response = service.submit_invoice(invoice)
            return invoice.status == ElectronicInvoiceStatus.VALIDATED
        except DGIError as e:
            logger.error(f"DGI submission failed: {e.message}")
            invoice.status = ElectronicInvoiceStatus.REJECTED
            invoice.rejection_reason = e.message
            invoice.save()
            return False

    def cancel_invoice(
        self,
        invoice: ElectronicInvoice,
        reason: str
    ) -> bool:
        """
        Cancel an electronic invoice.

        Args:
            invoice: Invoice to cancel
            reason: Cancellation reason

        Returns:
            bool: True if cancellation successful
        """
        if invoice.status == ElectronicInvoiceStatus.CANCELLED:
            return True

        # If validated with DGI, need to cancel there too
        if invoice.dgi_uid:
            try:
                config = DGIConfiguration.objects.get(business=self.business)
                service = DGIService(config)
                service.cancel_invoice(invoice.dgi_uid, reason)
            except (DGIConfiguration.DoesNotExist, DGIError) as e:
                logger.error(f"DGI cancellation failed: {e}")
                # Continue with local cancellation anyway

        invoice.status = ElectronicInvoiceStatus.CANCELLED
        invoice.rejection_reason = f"Cancelled: {reason}"
        invoice.save()
        return True

    def get_invoice_for_order(self, order: Order) -> Optional[ElectronicInvoice]:
        """
        Get electronic invoice for an order.

        Args:
            order: Order instance

        Returns:
            ElectronicInvoice or None
        """
        try:
            return ElectronicInvoice.objects.get(order=order)
        except ElectronicInvoice.DoesNotExist:
            return None

    def generate_pdf(self, invoice: ElectronicInvoice) -> str:
        """
        Generate PDF for an invoice.

        Args:
            invoice: Invoice to generate PDF for

        Returns:
            str: Path to generated PDF file
        """
        # TODO: Implement PDF generation using reportlab or weasyprint
        # For now, this is a placeholder
        raise NotImplementedError("PDF generation not yet implemented")
