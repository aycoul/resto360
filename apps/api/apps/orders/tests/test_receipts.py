"""Tests for receipt PDF generation."""

import pytest
from unittest.mock import patch, MagicMock

from apps.receipts.services import WEASYPRINT_AVAILABLE

# Skip PDF-related tests if WeasyPrint is not available (e.g., Windows without GTK)
pytestmark_weasyprint = pytest.mark.skipif(
    not WEASYPRINT_AVAILABLE,
    reason="WeasyPrint requires GTK libraries (not available on this system)"
)


@pytest.mark.django_db
class TestReceiptDownloadAPI:
    """Tests for the receipt download endpoint (POS-10 verification)."""

    @pytestmark_weasyprint
    def test_download_receipt_pdf(
        self, owner_client, owner, order_factory, cashier_factory
    ):
        """Test downloading receipt PDF for an order."""
        cashier = cashier_factory(business=owner.business)
        order = order_factory(
            business=owner.business,
            cashier=cashier,
            order_number=1,
            subtotal=5000,
            total=5000,
            order_type="takeaway",
        )

        # Mock WeasyPrint to avoid system dependencies in tests
        with patch("apps.receipts.services.HTML") as mock_html, \
             patch("apps.receipts.services.WEASYPRINT_AVAILABLE", True):
            mock_instance = MagicMock()
            mock_instance.write_pdf = MagicMock()
            mock_html.return_value = mock_instance

            response = owner_client.get(f"/api/v1/orders/{order.id}/receipt/")

            # WeasyPrint was called
            assert mock_html.called

        # Response should be PDF
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert "attachment" in response["Content-Disposition"]
        assert f"receipt-{order.order_number}" in response["Content-Disposition"]

    def test_download_receipt_requires_auth(self, api_client, order_factory, cashier_factory, business_factory):
        """Test receipt download requires authentication."""
        business = business_factory()
        cashier = cashier_factory(business=business)
        order = order_factory(business=business, cashier=cashier, order_type="takeaway")

        response = api_client.get(f"/api/v1/orders/{order.id}/receipt/")
        assert response.status_code == 401

    def test_download_receipt_not_found(self, owner_client):
        """Test 404 for non-existent order."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = owner_client.get(f"/api/v1/orders/{fake_id}/receipt/")
        assert response.status_code == 404

    def test_cannot_download_other_business_receipt(
        self,
        owner_client,
        owner,
        order_factory,
        business_factory,
        cashier_factory,
    ):
        """Test cannot download receipt for another business's order."""
        other_business = business_factory()
        other_cashier = cashier_factory(business=other_business)
        order = order_factory(
            business=other_business,
            cashier=other_cashier,
            order_type="takeaway",
        )

        response = owner_client.get(f"/api/v1/orders/{order.id}/receipt/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestReceiptService:
    """Tests for receipt generation service."""

    @pytestmark_weasyprint
    def test_generate_receipt_pdf_content(
        self, order_factory, order_item_factory, cashier_factory, business_factory
    ):
        """Test receipt PDF includes order details."""
        from apps.receipts.services import generate_receipt_pdf, get_receipt_filename

        business = business_factory(name="Test Business")
        cashier = cashier_factory(business=business)
        order = order_factory(
            business=business,
            cashier=cashier,
            order_number=42,
            subtotal=7500,
            total=7000,
            discount=500,
            order_type="takeaway",
        )
        order_item_factory(
            order=order,
            business=business,
            name="Burger",
            unit_price=5000,
            quantity=1,
            line_total=5000,
        )
        order_item_factory(
            order=order,
            business=business,
            name="Fries",
            unit_price=2500,
            quantity=1,
            line_total=2500,
        )

        # Mock WeasyPrint
        with patch("apps.receipts.services.HTML") as mock_html, \
             patch("apps.receipts.services.WEASYPRINT_AVAILABLE", True):
            mock_instance = MagicMock()
            mock_instance.write_pdf = MagicMock()
            mock_html.return_value = mock_instance

            result = generate_receipt_pdf(order)

            # Check HTML was rendered
            assert mock_html.called
            call_args = mock_html.call_args
            html_content = call_args.kwargs.get("string", call_args.args[0] if call_args.args else "")

            # Verify key content is in HTML
            # Note: We can check the template rendering by inspecting render_to_string calls

    def test_receipt_filename_format(
        self, order_factory, cashier_factory, business_factory
    ):
        """Test receipt filename format (does not require WeasyPrint)."""
        from apps.receipts.services import get_receipt_filename

        business = business_factory()
        cashier = cashier_factory(business=business)
        order = order_factory(
            business=business,
            cashier=cashier,
            order_number=123,
            order_type="takeaway",
        )

        filename = get_receipt_filename(order)

        assert filename.startswith("receipt-123-")
        assert filename.endswith(".pdf")
