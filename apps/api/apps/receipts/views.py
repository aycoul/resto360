"""Receipt views for RESTO360."""

from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.context import set_current_restaurant
from apps.orders.models import Order

from .services import generate_receipt_pdf, get_receipt_filename


class ReceiptDownloadView(APIView):
    """API endpoint to download receipt PDF for an order."""

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

    def get(self, request, order_id):
        """
        Generate and return PDF receipt for an order.

        Returns PDF file as attachment for download.
        """
        try:
            order = Order.objects.select_related(
                "restaurant", "table", "cashier"
            ).prefetch_related(
                "items__modifiers"
            ).get(
                id=order_id,
                restaurant=request.user.restaurant,
            )
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Generate PDF
        try:
            pdf_content = generate_receipt_pdf(order)
        except RuntimeError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        filename = get_receipt_filename(order)

        # Return as PDF response
        response = HttpResponse(pdf_content, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
