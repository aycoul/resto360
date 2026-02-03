"""QR code generation services for RESTO360."""

import io

import segno
from django.conf import settings


def generate_menu_qr(restaurant, format="png", scale=10, border=2):
    """
    Generate a QR code pointing to the restaurant's menu.

    Creates a QR code that links to the frontend menu URL for
    the given restaurant. Suitable for printing on tables or flyers.

    Args:
        restaurant: Restaurant instance
        format: Image format ('png', 'svg', 'eps')
        scale: Pixel size per module (1 module = 1 QR square)
        border: Number of quiet zone modules (white border)

    Returns:
        bytes: Image file content
    """
    # Build menu URL
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    menu_url = f"{frontend_url}/menu/{restaurant.slug}"

    # Generate QR code
    qr = segno.make(menu_url)

    # Render to bytes
    buffer = io.BytesIO()

    if format == "svg":
        qr.save(buffer, kind="svg", scale=scale, border=border)
    elif format == "eps":
        qr.save(buffer, kind="eps", scale=scale, border=border)
    else:
        # Default to PNG
        qr.save(buffer, kind="png", scale=scale, border=border, dark="#000000")

    buffer.seek(0)
    return buffer.getvalue()


def get_qr_content_type(format):
    """
    Get the content type for a QR code format.

    Args:
        format: Image format ('png', 'svg', 'eps')

    Returns:
        str: MIME content type
    """
    content_types = {
        "png": "image/png",
        "svg": "image/svg+xml",
        "eps": "application/postscript",
    }
    return content_types.get(format, "image/png")


def get_qr_filename(restaurant, format="png"):
    """
    Generate a filename for the QR code.

    Args:
        restaurant: Restaurant instance
        format: Image format

    Returns:
        str: Filename like "menu-qr-resto-name.png"
    """
    return f"menu-qr-{restaurant.slug}.{format}"
