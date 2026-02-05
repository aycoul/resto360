"""Tests for QR code generation."""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestMenuQRCodeAPI:
    """Tests for the menu QR code endpoint."""

    def test_generate_menu_qr_png(self, owner_client, owner):
        """Test generating menu QR code as PNG."""
        response = owner_client.get("/api/v1/menu-qr/")
        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"
        assert "attachment" in response["Content-Disposition"]
        assert owner.business.slug in response["Content-Disposition"]

    def test_generate_menu_qr_svg(self, owner_client, owner):
        """Test generating menu QR code as SVG."""
        response = owner_client.get("/api/v1/menu-qr/?output=svg")
        assert response.status_code == 200
        assert response["Content-Type"] == "image/svg+xml"

    def test_generate_menu_qr_inline(self, owner_client, owner):
        """Test generating menu QR code for inline display."""
        response = owner_client.get("/api/v1/menu-qr/?inline=true")
        assert response.status_code == 200
        assert "inline" in response["Content-Disposition"]

    def test_qr_custom_scale(self, owner_client, owner):
        """Test QR code with custom scale."""
        response = owner_client.get("/api/v1/menu-qr/?scale=20")
        assert response.status_code == 200

    def test_qr_custom_border(self, owner_client, owner):
        """Test QR code with custom border."""
        response = owner_client.get("/api/v1/menu-qr/?border=4")
        assert response.status_code == 200

    def test_menu_qr_requires_auth(self, api_client):
        """Test QR code requires authentication."""
        response = api_client.get("/api/v1/menu-qr/")
        assert response.status_code == 401

    def test_invalid_format_defaults_to_png(self, owner_client, owner):
        """Test invalid format defaults to PNG."""
        response = owner_client.get("/api/v1/menu-qr/?output=invalid")
        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"


@pytest.mark.django_db
class TestQRCodeService:
    """Tests for QR code generation service."""

    def test_generate_menu_qr_content(self, business):
        """Test QR code contains correct URL."""
        from apps.qr.services import generate_menu_qr

        qr_content = generate_menu_qr(business)

        # Should return bytes (PNG image)
        assert isinstance(qr_content, bytes)
        assert len(qr_content) > 0

    def test_get_qr_content_type(self):
        """Test content type mapping."""
        from apps.qr.services import get_qr_content_type

        assert get_qr_content_type("png") == "image/png"
        assert get_qr_content_type("svg") == "image/svg+xml"
        assert get_qr_content_type("eps") == "application/postscript"
        assert get_qr_content_type("unknown") == "image/png"

    def test_get_qr_filename(self, business):
        """Test QR code filename format."""
        from apps.qr.services import get_qr_filename

        filename = get_qr_filename(business)
        assert filename == f"menu-qr-{business.slug}.png"

        filename_svg = get_qr_filename(business, "svg")
        assert filename_svg == f"menu-qr-{business.slug}.svg"
