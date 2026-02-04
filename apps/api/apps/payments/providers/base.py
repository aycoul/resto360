"""Base classes for payment providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ProviderStatus(str, Enum):
    """Status returned by payment providers."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class PaymentResult:
    """Result of a payment initiation or status check."""

    provider_reference: str
    status: ProviderStatus
    redirect_url: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[dict] = None


@dataclass
class RefundResult:
    """Result of a refund request."""

    success: bool
    provider_reference: Optional[str] = None
    error_message: Optional[str] = None


class PaymentProvider(ABC):
    """
    Abstract base class for payment providers.

    All payment providers (Wave, Orange, MTN, Cash) must implement this interface.
    """

    @property
    @abstractmethod
    def provider_code(self) -> str:
        """Return the provider code (e.g., 'wave', 'orange', 'mtn', 'cash')."""
        pass

    @abstractmethod
    def initiate_payment(
        self,
        amount: int,
        currency: str,
        order_reference: str,
        customer_phone: str,
        idempotency_key: str,
        callback_url: str,
        success_url: str,
        error_url: str,
    ) -> PaymentResult:
        """
        Initiate a payment with the provider.

        Args:
            amount: Payment amount in smallest currency unit (XOF integer)
            currency: Currency code (e.g., 'XOF')
            order_reference: Reference to the order being paid
            customer_phone: Customer phone number for mobile money
            idempotency_key: Unique key to prevent duplicate payments
            callback_url: URL for webhook notifications
            success_url: URL to redirect after successful payment
            error_url: URL to redirect after failed payment

        Returns:
            PaymentResult with provider reference and status
        """
        pass

    @abstractmethod
    def check_status(self, provider_reference: str) -> PaymentResult:
        """
        Check the status of a payment with the provider.

        Args:
            provider_reference: The provider's reference for the payment

        Returns:
            PaymentResult with current status
        """
        pass

    @abstractmethod
    def process_refund(
        self, provider_reference: str, amount: Optional[int] = None
    ) -> RefundResult:
        """
        Process a refund for a payment.

        Args:
            provider_reference: The provider's reference for the original payment
            amount: Optional partial refund amount (full refund if not specified)

        Returns:
            RefundResult indicating success or failure
        """
        pass

    @abstractmethod
    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """
        Verify the authenticity of a webhook request.

        Args:
            headers: Request headers
            body: Raw request body

        Returns:
            True if the webhook is authentic, False otherwise
        """
        pass

    @abstractmethod
    def parse_webhook(self, body: bytes) -> dict:
        """
        Parse a webhook request body.

        Args:
            body: Raw request body

        Returns:
            Parsed webhook data as a dictionary
        """
        pass
