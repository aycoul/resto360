"""
DGI API Service for Ivory Coast Electronic Invoice Compliance.

Handles communication with the DGI (Direction Générale des Impôts) API
for electronic invoice validation according to FNE/RNE requirements.
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import requests
from django.conf import settings
from django.utils import timezone

from ..models import DGIConfiguration, ElectronicInvoice, ElectronicInvoiceStatus

logger = logging.getLogger(__name__)


class DGIError(Exception):
    """Base exception for DGI API errors."""

    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class DGIService:
    """Service for Ivory Coast DGI electronic invoice submission."""

    # API URLs
    SANDBOX_URL = "https://test-api.dgi.gouv.ci/facture/v1"
    PRODUCTION_URL = "https://api.dgi.gouv.ci/facture/v1"

    # Timeout settings
    TIMEOUT = 30  # seconds

    def __init__(self, config: DGIConfiguration):
        """
        Initialize DGI service with configuration.

        Args:
            config: DGIConfiguration instance for the business
        """
        self.config = config
        self.base_url = self.PRODUCTION_URL if config.is_production else self.SANDBOX_URL

    def submit_invoice(self, invoice: ElectronicInvoice) -> dict:
        """
        Submit invoice to DGI for validation.

        Args:
            invoice: ElectronicInvoice instance to submit

        Returns:
            dict: API response with DGI UID and validation status

        Raises:
            DGIError: If submission fails
        """
        payload = self._build_invoice_payload(invoice)

        # Store request for debugging
        invoice.api_request = payload
        invoice.save(update_fields=["api_request", "updated_at"])

        try:
            response = self._make_request("POST", "/invoices", payload)

            # Store response
            invoice.api_response = response
            invoice.save(update_fields=["api_response", "updated_at"])

            # Update invoice with DGI data
            if response.get("status") == "accepted":
                invoice.dgi_uid = response.get("uid", "")
                invoice.dgi_qr_code = response.get("qr_code", "")
                invoice.dgi_signature = response.get("signature", "")
                invoice.dgi_validation_date = timezone.now()
                invoice.status = ElectronicInvoiceStatus.VALIDATED
            else:
                invoice.status = ElectronicInvoiceStatus.REJECTED
                invoice.rejection_reason = response.get("error_message", "Unknown error")

            invoice.save()
            return response

        except requests.RequestException as e:
            logger.error(f"DGI API request failed: {e}")
            invoice.status = ElectronicInvoiceStatus.REJECTED
            invoice.rejection_reason = str(e)
            invoice.save()
            raise DGIError(f"API request failed: {e}")

    def get_invoice_status(self, dgi_uid: str) -> dict:
        """
        Check invoice validation status.

        Args:
            dgi_uid: DGI unique identifier

        Returns:
            dict: Status information from DGI
        """
        return self._make_request("GET", f"/invoices/{dgi_uid}/status")

    def cancel_invoice(self, dgi_uid: str, reason: str) -> dict:
        """
        Request invoice cancellation.

        Args:
            dgi_uid: DGI unique identifier
            reason: Cancellation reason

        Returns:
            dict: Cancellation response
        """
        return self._make_request(
            "POST",
            f"/invoices/{dgi_uid}/cancel",
            {"reason": reason}
        )

    def validate_credentials(self) -> bool:
        """
        Validate DGI API credentials.

        Returns:
            bool: True if credentials are valid
        """
        try:
            self._make_request("GET", "/auth/validate")
            return True
        except DGIError:
            return False

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict = None
    ) -> dict:
        """
        Make authenticated request to DGI API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request body data

        Returns:
            dict: JSON response

        Raises:
            DGIError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._build_headers(data)

        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=self.TIMEOUT,
            )

            # Log for debugging
            logger.info(f"DGI API {method} {endpoint}: {response.status_code}")

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise DGIError(
                    message=error_data.get("message", f"HTTP {response.status_code}"),
                    code=error_data.get("code"),
                    details=error_data,
                )

            return response.json() if response.content else {}

        except requests.Timeout:
            raise DGIError("Request timed out")
        except requests.ConnectionError:
            raise DGIError("Connection failed")
        except json.JSONDecodeError:
            raise DGIError("Invalid JSON response")

    def _build_headers(self, data: dict = None) -> dict:
        """
        Build authenticated headers for DGI API.

        Args:
            data: Request body for signature

        Returns:
            dict: HTTP headers
        """
        timestamp = datetime.utcnow().isoformat()

        # Generate signature (HMAC-SHA256)
        message = f"{self.config.taxpayer_id}{timestamp}"
        if data:
            message += json.dumps(data, sort_keys=True)

        signature = hmac.new(
            self.config.api_secret.encode() if self.config.api_secret else b"",
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        return {
            "Content-Type": "application/json",
            "X-DGI-API-Key": self.config.api_key,
            "X-DGI-Taxpayer-ID": self.config.taxpayer_id,
            "X-DGI-Timestamp": timestamp,
            "X-DGI-Signature": signature,
        }

    def _build_invoice_payload(self, invoice: ElectronicInvoice) -> dict:
        """
        Build DGI-compliant invoice payload.

        Args:
            invoice: ElectronicInvoice instance

        Returns:
            dict: Invoice payload for DGI API
        """
        return {
            "numero_facture": invoice.invoice_number,
            "date_facture": invoice.invoice_date.isoformat(),
            "type_facture": "FNE",  # Facture Normalisée Électronique
            "emetteur": {
                "ncc": invoice.seller_ncc,
                "raison_sociale": invoice.seller_name,
                "adresse": invoice.seller_address,
                "telephone": invoice.seller_phone,
                "email": invoice.seller_email,
            },
            "client": {
                "nom": invoice.customer_name,
                "ncc": invoice.customer_ncc or None,
                "adresse": invoice.customer_address,
                "telephone": invoice.customer_phone,
                "email": invoice.customer_email,
            },
            "lignes": [
                {
                    "description": line.description,
                    "quantite": float(line.quantity),
                    "prix_unitaire_ht": line.unit_price_ht,
                    "taux_tva": float(line.tva_rate),
                    "montant_tva": line.tva_amount,
                    "montant_ht": line.line_total_ht,
                    "montant_ttc": line.line_total_ttc,
                }
                for line in invoice.lines.all()
            ],
            "totaux": {
                "montant_ht": invoice.subtotal_ht,
                "montant_remise": invoice.discount_amount,
                "montant_tva": invoice.tva_amount,
                "montant_ttc": invoice.total_ttc,
            },
            "taux_tva_global": float(invoice.tva_rate),
        }
