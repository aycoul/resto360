"""Payment models for RESTO360."""

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django_fsm import FSMField, transition

from apps.core.managers import TenantManager
from apps.core.models import TenantModel


class PaymentStatus(models.TextChoices):
    """Payment status enumeration."""

    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"
    PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"
    EXPIRED = "expired", "Expired"


class PaymentMethod(TenantModel):
    """Payment method configuration per restaurant."""

    provider_code = models.CharField(
        max_length=20,
        help_text="Provider identifier: wave, orange, mtn, cash",
    )
    name = models.CharField(
        max_length=100,
        help_text="Display name for the payment method",
    )
    is_active = models.BooleanField(default=True)
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Provider-specific configuration (NOT secrets)",
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which to display payment methods",
    )

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["display_order", "name"]
        unique_together = [["restaurant", "provider_code"]]

    def __str__(self):
        return f"{self.name} ({self.provider_code})"


class Payment(TenantModel):
    """A payment for an order."""

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.PositiveIntegerField(
        help_text="Payment amount in XOF (integer)",
    )
    status = FSMField(
        default=PaymentStatus.PENDING,
        choices=PaymentStatus.choices,
        protected=True,
    )
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique key to prevent duplicate payments",
    )
    provider_code = models.CharField(
        max_length=20,
        help_text="Provider that processed this payment",
    )
    provider_reference = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Reference from the payment provider",
    )
    provider_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw response from the provider",
    )
    error_code = models.CharField(
        max_length=100,
        blank=True,
        help_text="Error code if payment failed",
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if payment failed",
    )
    refunded_amount = models.PositiveIntegerField(
        default=0,
        help_text="Amount refunded in XOF",
    )
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-initiated_at"]
        indexes = [
            models.Index(fields=["restaurant", "status"]),
            models.Index(fields=["provider_reference"]),
        ]

    def __str__(self):
        return f"Payment {self.idempotency_key} - {self.amount} XOF ({self.status})"

    # FSM Transitions

    @transition(field=status, source=PaymentStatus.PENDING, target=PaymentStatus.PROCESSING)
    def start_processing(self):
        """Transition from PENDING to PROCESSING."""
        pass

    @transition(field=status, source=PaymentStatus.PROCESSING, target=PaymentStatus.SUCCESS)
    def mark_success(self):
        """Transition from PROCESSING to SUCCESS."""
        self.completed_at = timezone.now()

    @transition(field=status, source=PaymentStatus.PROCESSING, target=PaymentStatus.FAILED)
    def mark_failed(self, error_code: str = "", error_message: str = ""):
        """Transition from PROCESSING to FAILED."""
        self.error_code = error_code
        self.error_message = error_message
        self.completed_at = timezone.now()

    @transition(field=status, source=PaymentStatus.PROCESSING, target=PaymentStatus.EXPIRED)
    def mark_expired(self):
        """Transition from PROCESSING to EXPIRED."""
        self.completed_at = timezone.now()

    @transition(field=status, source=PaymentStatus.SUCCESS, target=PaymentStatus.REFUNDED)
    def mark_refunded(self):
        """Transition from SUCCESS to REFUNDED (full refund)."""
        self.refunded_amount = self.amount

    @transition(field=status, source=PaymentStatus.SUCCESS, target=PaymentStatus.PARTIALLY_REFUNDED)
    def mark_partially_refunded(self, refund_amount: int):
        """Transition from SUCCESS to PARTIALLY_REFUNDED."""
        self.refunded_amount = refund_amount


class CashDrawerSession(TenantModel):
    """A cash drawer session for tracking cash payments."""

    cashier = models.ForeignKey(
        "authentication.User",
        on_delete=models.PROTECT,
        related_name="cash_drawer_sessions",
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    opening_balance = models.PositiveIntegerField(
        help_text="Opening balance in XOF",
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closing_balance = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Actual closing balance in XOF",
    )
    expected_balance = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Expected closing balance based on transactions",
    )
    variance = models.IntegerField(
        null=True,
        blank=True,
        help_text="Difference between actual and expected (can be negative)",
    )
    variance_notes = models.TextField(
        blank=True,
        help_text="Notes explaining any variance",
    )

    # Use standard manager for related lookups (Django uses first manager)
    all_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self):
        status = "Open" if self.is_open else "Closed"
        return f"Cash Drawer - {self.cashier} ({status})"

    @property
    def is_open(self) -> bool:
        """Check if the cash drawer session is still open."""
        return self.closed_at is None

    def close(self, closing_balance: int, notes: str = "") -> None:
        """
        Close the cash drawer session.

        Args:
            closing_balance: The actual counted closing balance in XOF
            notes: Optional notes explaining any variance
        """
        # Calculate expected balance: opening + successful cash payments
        cash_payments_total = Payment.all_objects.filter(
            restaurant=self.restaurant,
            provider_code="cash",
            status=PaymentStatus.SUCCESS,
            completed_at__gte=self.opened_at,
            completed_at__lte=timezone.now(),
        ).aggregate(total=Sum("amount"))["total"] or 0

        self.expected_balance = self.opening_balance + cash_payments_total
        self.closing_balance = closing_balance
        self.variance = closing_balance - self.expected_balance
        self.variance_notes = notes
        self.closed_at = timezone.now()
