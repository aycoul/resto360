"""Invoicing views for BIZ360."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.context import set_current_business

from .models import DGIConfiguration, ElectronicInvoice
from .serializers import (
    DGIConfigurationSerializer,
    DGIConfigurationWriteSerializer,
    ElectronicInvoiceSerializer,
    InvoiceCancelSerializer,
    InvoiceCreateSerializer,
)
from .services import InvoiceService


class DGIConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for DGI configuration management."""

    permission_classes = [IsAuthenticated]
    serializer_class = DGIConfigurationSerializer

    def get_queryset(self):
        return DGIConfiguration.objects.filter(business=self.request.user.business)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DGIConfigurationWriteSerializer
        return DGIConfigurationSerializer

    @action(detail=True, methods=["post"])
    def validate_credentials(self, request, pk=None):
        """Validate DGI API credentials."""
        config = self.get_object()
        from .services import DGIService
        service = DGIService(config)
        is_valid = service.validate_credentials()
        return Response({"valid": is_valid})


class ElectronicInvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for electronic invoices."""

    permission_classes = [IsAuthenticated]
    serializer_class = ElectronicInvoiceSerializer
    http_method_names = ["get", "post"]  # No direct update/delete

    def get_queryset(self):
        # Set tenant context
        set_current_business(self.request.user.business)
        return ElectronicInvoice.objects.filter(
            business=self.request.user.business
        ).select_related("order").prefetch_related("lines")

    def get_serializer_class(self):
        if self.action == "create":
            return InvoiceCreateSerializer
        return ElectronicInvoiceSerializer

    def create(self, request, *args, **kwargs):
        """Create invoice from order."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save()
        output = ElectronicInvoiceSerializer(invoice)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def submit_to_dgi(self, request, pk=None):
        """Submit invoice to DGI for validation."""
        invoice = self.get_object()
        service = InvoiceService(request.user.business)
        success = service.submit_to_dgi(invoice)

        # Refresh from DB
        invoice.refresh_from_db()
        serializer = self.get_serializer(invoice)

        return Response({
            "success": success,
            "invoice": serializer.data,
        })

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel an invoice."""
        invoice = self.get_object()
        serializer = InvoiceCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InvoiceService(request.user.business)
        success = service.cancel_invoice(invoice, serializer.validated_data["reason"])

        invoice.refresh_from_db()
        output = self.get_serializer(invoice)

        return Response({
            "success": success,
            "invoice": output.data,
        })

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        """Download invoice PDF."""
        invoice = self.get_object()

        if not invoice.pdf_file:
            # Generate PDF on-the-fly
            try:
                service = InvoiceService(request.user.business)
                service.generate_pdf(invoice)
            except NotImplementedError:
                return Response(
                    {"error": "PDF generation not yet implemented"},
                    status=status.HTTP_501_NOT_IMPLEMENTED,
                )

        # Return file URL for now
        return Response({"pdf_url": invoice.pdf_file.url if invoice.pdf_file else None})
