"""Receipt generation services for RESTO360."""

import io
from pathlib import Path

from django.template.loader import render_to_string
from weasyprint import HTML


def generate_receipt_pdf(order):
    """
    Generate a PDF receipt for an order.

    Uses WeasyPrint to render HTML template to PDF optimized for
    80mm thermal receipt printers.

    Args:
        order: Order instance with related items, modifiers, and restaurant

    Returns:
        bytes: PDF file content
    """
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
