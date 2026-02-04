"""Order services for BIZ360 (formerly RESTO360)."""

from django.db import transaction
from django.utils import timezone

from .models import DailySequence, InvoiceSequence


def get_next_order_number(business):
    """
    Get the next order number for a business.

    Uses SELECT FOR UPDATE to ensure atomic increment even under
    concurrent order creation. Order numbers reset daily.

    Args:
        business: Business instance

    Returns:
        int: Next order number for today
    """
    today = timezone.localdate()

    with transaction.atomic():
        # Use select_for_update to lock the row
        sequence, created = DailySequence.objects.select_for_update().get_or_create(
            business=business,
            date=today,
            defaults={"last_number": 0},
        )

        sequence.last_number += 1
        sequence.save(update_fields=["last_number", "updated_at"])

        return sequence.last_number


def generate_invoice_number(business):
    """
    Generate sequential invoice number for a business (never resets).

    Format: BIZ-{business_id_prefix}-{year}-{sequence}
    Example: BIZ-A1B2C3-2026-000001

    Args:
        business: Business instance

    Returns:
        str: Invoice number
    """
    year = timezone.now().year
    prefix = f"BIZ-{business.id.hex[:6].upper()}-{year}"

    with transaction.atomic():
        sequence, created = InvoiceSequence.objects.select_for_update().get_or_create(
            business=business,
            year=year,
            defaults={"last_number": 0},
        )

        sequence.last_number += 1
        sequence.save(update_fields=["last_number", "updated_at"])

        return f"{prefix}-{sequence.last_number:06d}"


def calculate_order_totals(order):
    """
    Calculate and update order subtotal, tax, and total.

    Args:
        order: Order instance
    """
    # First, recalculate each item's line total
    for item in order.items.all():
        item.calculate_line_total()
        item.save(update_fields=["modifiers_total", "line_total", "updated_at"])

    # Then calculate order totals (includes tax calculation)
    order.calculate_totals()
    order.save(update_fields=[
        "subtotal", "subtotal_ht", "tax_amount", "total", "updated_at"
    ])
