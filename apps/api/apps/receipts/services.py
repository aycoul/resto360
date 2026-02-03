"""Receipt generation services for RESTO360."""

import io
import logging
from pathlib import Path

from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

# WeasyPrint requires GTK libraries which may not be available on all platforms
# (particularly Windows without GTK installed)
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except OSError as e:
    logger.warning(f"WeasyPrint not available (missing GTK libraries): {e}")
    HTML = None
    WEASYPRINT_AVAILABLE = False


def generate_receipt_pdf(order):
    """
    Generate a PDF receipt for an order.

    Uses WeasyPrint to render HTML template to PDF optimized for
    80mm thermal receipt printers.

    Args:
        order: Order instance with related items, modifiers, and restaurant

    Returns:
        bytes: PDF file content

    Raises:
        RuntimeError: If WeasyPrint is not available (missing GTK libraries)
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            "PDF generation is not available. WeasyPrint requires GTK libraries. "
            "On Windows, install GTK3: https://github.com/nicowilliams/gtk4-windows"
        )

    # Ensure order has all related data loaded
    restaurant = order.restaurant

    # Render HTML template
    html_content = render_to_string(
        "receipts/receipt.html",
        {
            "order": order,
            "restaurant": restaurant,
        },
    )

    # Generate PDF
    html = HTML(string=html_content)
    pdf_buffer = io.BytesIO()
    html.write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    return pdf_buffer.getvalue()


def get_receipt_filename(order):
    """
    Generate a filename for the receipt PDF.

    Args:
        order: Order instance

    Returns:
        str: Filename like "receipt-123-2024-01-15.pdf"
    """
    date_str = order.created_at.strftime("%Y-%m-%d")
    return f"receipt-{order.order_number}-{date_str}.pdf"
