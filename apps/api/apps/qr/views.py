"""QR code views for RESTO360."""

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.context import set_current_restaurant

from .services import generate_menu_qr, get_qr_content_type, get_qr_filename


class MenuQRCodeView(APIView):
    """API endpoint to generate QR code for restaurant menu."""

    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        """Set tenant context after authentication."""
        super().initial(request, *args, **kwargs)
        if request.user.is_authenticated:
            if hasattr(request.user, "restaurant") and request.user.restaurant:
                set_current_restaurant(request.user.restaurant)

    def finalize_response(self, request, response, *args, **kwargs):
        """Clear tenant context after response."""
        response = super().finalize_response(request, response, *args, **kwargs)
        set_current_restaurant(None)
        return response

    def get(self, request):
        """
        Generate and return QR code for the restaurant's menu.

        Query parameters:
            output: 'png' (default), 'svg', or 'eps' (image format)
            scale: Pixel size per module (default: 10)
            border: Quiet zone modules (default: 2)

        Returns image file as attachment for download or inline display.
        """
        restaurant = request.user.restaurant

        # Parse query parameters
        # Note: Use 'output' instead of 'format' to avoid conflict with DRF content negotiation
        output_format = request.query_params.get("output", "png").lower()
        if output_format not in ("png", "svg", "eps"):
            output_format = "png"

        try:
            scale = int(request.query_params.get("scale", 10))
            scale = max(1, min(scale, 50))  # Clamp between 1-50
        except (ValueError, TypeError):
            scale = 10

        try:
            border = int(request.query_params.get("border", 2))
            border = max(0, min(border, 10))  # Clamp between 0-10
        except (ValueError, TypeError):
            border = 2

        # Check if inline display requested
        inline = request.query_params.get("inline", "false").lower() == "true"

        # Generate QR code
        qr_content = generate_menu_qr(
            restaurant,
            format=output_format,
            scale=scale,
            border=border,
        )

        content_type = get_qr_content_type(output_format)
        filename = get_qr_filename(restaurant, output_format)

        # Return as image response
        response = HttpResponse(qr_content, content_type=content_type)
        disposition = "inline" if inline else "attachment"
        response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
        return response
