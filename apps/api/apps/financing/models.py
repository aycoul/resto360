"""
Models for Restaurant Financing.

This module provides models for managing loans, credit scoring,
loan applications, repayments, and finance partner integrations.
"""

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class FinancePartner(BaseModel):
    """
    Finance partners (banks, microfinance institutions) that provide loans.
    """

    class PartnerType(models.TextChoices):
        BANK = "bank", "Bank"
        MICROFINANCE = "microfinance", "Microfinance Institution"
        FINTECH = "fintech", "Fintech"
        INVESTOR = "investor", "Investor"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    partner_type = models.CharField(
        max_length=20,
        choices=PartnerType.choices,
        default=PartnerType.MICROFINANCE,
    )
    description = models.TextField(blank=True)

    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    contact_person = models.CharField(max_length=200, blank=True)

    # Logo/Branding
    logo = models.ImageField(upload_to="financing/partners/", blank=True, null=True)

    # Loan Parameters
    min_loan_amount = models.DecimalField(
        max_digits=12, decimal_places=0, default=100000,
        help_text="Minimum loan amount in XOF"
    )
    max_loan_amount = models.DecimalField(
        max_digits=12, decimal_places=0, default=10000000,
        help_text="Maximum loan amount in XOF"
    )
    min_interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=5,
        help_text="Minimum annual interest rate %"
    )
    max_interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=25,
        help_text="Maximum annual interest rate %"
    )
    min_term_months = models.PositiveSmallIntegerField(default=1)
    max_term_months = models.PositiveSmallIntegerField(default=24)

    # Eligibility
    min_credit_score = models.PositiveSmallIntegerField(
        default=500,
        help_text="Minimum credit score required (0-1000)"
    )
    min_platform_tenure_days = models.PositiveIntegerField(
        default=90,
        help_text="Minimum days on platform"
    )
    min_monthly_revenue = models.DecimalField(
        max_digits=12, decimal_places=0, default=500000,
        help_text="Minimum monthly revenue in XOF"
    )

    # API Integration
    api_endpoint = models.URLField(blank=True)
    api_key = models.CharField(max_length=200, blank=True)
    webhook_secret = models.CharField(max_length=200, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # Stats
    total_loans_disbursed = models.PositiveIntegerField(default=0)
    total_amount_disbursed = models.DecimalField(max_digits=14, decimal_places=0, default=0)

    class Meta:
        ordering = ["-is_featured", "name"]

    def __str__(self):
        return self.name


class CreditScore(BaseModel):
    """
    Credit score for a restaurant, calculated from platform data.

    Score is on a 0-1000 scale:
    - 0-300: Poor
    - 301-500: Fair
    - 501-700: Good
    - 701-850: Very Good
    - 851-1000: Excellent
    """

    restaurant = models.OneToOneField(
        "authentication.Restaurant",
        on_delete=models.CASCADE,
        related_name="credit_score",
    )

    # Overall score (0-1000)
    score = models.PositiveSmallIntegerField(default=0)
    score_band = models.CharField(
        max_length=20,
        choices=[
            ("poor", "Poor"),
            ("fair", "Fair"),
            ("good", "Good"),
            ("very_good", "Very Good"),
            ("excellent", "Excellent"),
        ],
        default="fair",
    )

    # Component scores (each 0-100, weighted to make total)
    revenue_score = models.PositiveSmallIntegerField(
        default=0,
        help_text="Based on monthly revenue consistency and growth"
    )
    payment_score = models.PositiveSmallIntegerField(
        default=0,
        help_text="Based on payment processing history"
    )
    order_score = models.PositiveSmallIntegerField(
        default=0,
        help_text="Based on order volume and consistency"
    )
    tenure_score = models.PositiveSmallIntegerField(
        default=0,
        help_text="Based on time on platform"
    )
    activity_score = models.PositiveSmallIntegerField(
        default=0,
        help_text="Based on platform engagement"
    )

    # Underlying metrics
    avg_monthly_revenue = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    revenue_growth_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Month-over-month growth rate %"
    )
    avg_monthly_orders = models.PositiveIntegerField(default=0)
    platform_tenure_days = models.PositiveIntegerField(default=0)
    payment_success_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Percentage of successful payments"
    )
    active_days_ratio = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Ratio of days with orders to total days"
    )

    # Loan history
    total_loans_taken = models.PositiveSmallIntegerField(default=0)
    loans_repaid_on_time = models.PositiveSmallIntegerField(default=0)
    loans_defaulted = models.PositiveSmallIntegerField(default=0)
    current_outstanding = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    # Last calculation
    last_calculated = models.DateTimeField(auto_now=True)
    calculation_notes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Credit scores"

    def __str__(self):
        return f"{self.restaurant.name}: {self.score} ({self.score_band})"

    def calculate_score(self):
        """Recalculate the credit score from component scores."""
        # Weights for each component (total = 100%)
        weights = {
            'revenue': 0.30,
            'payment': 0.20,
            'order': 0.20,
            'tenure': 0.15,
            'activity': 0.15,
        }

        # Calculate weighted score (components are 0-100, result is 0-1000)
        self.score = int(
            (self.revenue_score * weights['revenue'] +
             self.payment_score * weights['payment'] +
             self.order_score * weights['order'] +
             self.tenure_score * weights['tenure'] +
             self.activity_score * weights['activity']) * 10
        )

        # Adjust for loan history
        if self.loans_defaulted > 0:
            self.score = int(self.score * 0.7)  # 30% penalty for defaults
        elif self.loans_repaid_on_time > 0:
            self.score = min(1000, int(self.score * 1.1))  # 10% bonus for good history

        # Determine score band
        if self.score <= 300:
            self.score_band = 'poor'
        elif self.score <= 500:
            self.score_band = 'fair'
        elif self.score <= 700:
            self.score_band = 'good'
        elif self.score <= 850:
            self.score_band = 'very_good'
        else:
            self.score_band = 'excellent'

        self.save()


class LoanProduct(BaseModel):
    """
    Loan products offered by finance partners.
    """

    class ProductType(models.TextChoices):
        WORKING_CAPITAL = "working_capital", "Working Capital"
        EQUIPMENT = "equipment", "Equipment Financing"
        EXPANSION = "expansion", "Expansion Loan"
        INVENTORY = "inventory", "Inventory Financing"
        EMERGENCY = "emergency", "Emergency Fund"

    partner = models.ForeignKey(
        FinancePartner,
        on_delete=models.CASCADE,
        related_name="loan_products",
    )

    name = models.CharField(max_length=200)
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.WORKING_CAPITAL,
    )
    description = models.TextField(blank=True)

    # Terms
    min_amount = models.DecimalField(max_digits=12, decimal_places=0)
    max_amount = models.DecimalField(max_digits=12, decimal_places=0)
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Annual interest rate %"
    )
    term_months = models.PositiveSmallIntegerField()

    # Fees
    origination_fee = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Percentage of loan amount"
    )
    late_fee = models.DecimalField(
        max_digits=10, decimal_places=0, default=0,
        help_text="Fixed late payment fee in XOF"
    )

    # Repayment
    repayment_frequency = models.CharField(
        max_length=20,
        choices=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("biweekly", "Bi-weekly"),
            ("monthly", "Monthly"),
        ],
        default="daily",
    )
    auto_deduct = models.BooleanField(
        default=True,
        help_text="Automatically deduct from daily sales"
    )
    auto_deduct_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=10,
        help_text="Percentage of daily sales to deduct"
    )

    # Eligibility
    min_credit_score = models.PositiveSmallIntegerField(default=500)
    min_monthly_revenue = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["partner", "name"]

    def __str__(self):
        return f"{self.partner.name} - {self.name}"


class LoanApplication(BaseModel):
    """
    Loan application submitted by a restaurant.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"
        DISBURSED = "disbursed", "Disbursed"

    # Application reference
    application_number = models.CharField(max_length=50, unique=True)

    restaurant = models.ForeignKey(
        "authentication.Restaurant",
        on_delete=models.PROTECT,
        related_name="loan_applications",
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="loan_applications",
    )

    # Loan details
    partner = models.ForeignKey(
        FinancePartner,
        on_delete=models.PROTECT,
        related_name="applications",
    )
    loan_product = models.ForeignKey(
        LoanProduct,
        on_delete=models.SET_NULL,
        null=True,
        related_name="applications",
    )

    amount_requested = models.DecimalField(max_digits=12, decimal_places=0)
    term_months = models.PositiveSmallIntegerField()
    purpose = models.CharField(
        max_length=50,
        choices=[
            ("working_capital", "Working Capital"),
            ("equipment", "Equipment Purchase"),
            ("expansion", "Business Expansion"),
            ("inventory", "Inventory"),
            ("renovation", "Renovation"),
            ("marketing", "Marketing"),
            ("other", "Other"),
        ],
    )
    purpose_details = models.TextField(blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    # Credit assessment at time of application
    credit_score_at_application = models.PositiveSmallIntegerField(default=0)
    monthly_revenue_at_application = models.DecimalField(
        max_digits=12, decimal_places=0, default=0
    )

    # Offer (if approved)
    amount_approved = models.DecimalField(
        max_digits=12, decimal_places=0, null=True, blank=True
    )
    interest_rate_offered = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    term_months_approved = models.PositiveSmallIntegerField(null=True, blank=True)
    monthly_payment = models.DecimalField(
        max_digits=10, decimal_places=0, null=True, blank=True
    )
    total_repayment = models.DecimalField(
        max_digits=12, decimal_places=0, null=True, blank=True
    )

    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    disbursed_at = models.DateTimeField(null=True, blank=True)

    # Review
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_applications",
    )
    review_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    # Documents
    documents = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["restaurant", "status"]),
            models.Index(fields=["partner", "status"]),
            models.Index(fields=["application_number"]),
        ]

    def __str__(self):
        return f"{self.application_number} - {self.restaurant.name}"

    def save(self, *args, **kwargs):
        if not self.application_number:
            today = timezone.now().strftime("%Y%m%d")
            count = LoanApplication.objects.filter(
                application_number__startswith=f"LA-{today}"
            ).count()
            self.application_number = f"LA-{today}-{count + 1:04d}"
        super().save(*args, **kwargs)


class Loan(BaseModel):
    """
    Active loan after disbursement.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAID_OFF = "paid_off", "Paid Off"
        DEFAULTED = "defaulted", "Defaulted"
        RESTRUCTURED = "restructured", "Restructured"

    # Loan reference
    loan_number = models.CharField(max_length=50, unique=True)

    application = models.OneToOneField(
        LoanApplication,
        on_delete=models.PROTECT,
        related_name="loan",
    )
    restaurant = models.ForeignKey(
        "authentication.Restaurant",
        on_delete=models.PROTECT,
        related_name="loans",
    )
    partner = models.ForeignKey(
        FinancePartner,
        on_delete=models.PROTECT,
        related_name="loans",
    )

    # Loan terms
    principal = models.DecimalField(max_digits=12, decimal_places=0)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.PositiveSmallIntegerField()
    origination_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    # Calculated amounts
    total_interest = models.DecimalField(max_digits=12, decimal_places=0)
    total_repayment = models.DecimalField(max_digits=12, decimal_places=0)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=0)

    # Repayment tracking
    amount_disbursed = models.DecimalField(max_digits=12, decimal_places=0)
    amount_repaid = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=0)
    next_payment_date = models.DateField()
    next_payment_amount = models.DecimalField(max_digits=10, decimal_places=0)

    # Auto-deduction
    auto_deduct_enabled = models.BooleanField(default=True)
    auto_deduct_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=10
    )

    # Dates
    disbursement_date = models.DateField()
    first_payment_date = models.DateField()
    maturity_date = models.DateField()
    paid_off_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    days_overdue = models.PositiveIntegerField(default=0)
    missed_payments = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-disbursement_date"]
        indexes = [
            models.Index(fields=["restaurant", "status"]),
            models.Index(fields=["partner", "status"]),
            models.Index(fields=["loan_number"]),
            models.Index(fields=["next_payment_date"]),
        ]

    def __str__(self):
        return f"{self.loan_number} - {self.restaurant.name}"

    def save(self, *args, **kwargs):
        if not self.loan_number:
            today = timezone.now().strftime("%Y%m%d")
            count = Loan.objects.filter(
                loan_number__startswith=f"LN-{today}"
            ).count()
            self.loan_number = f"LN-{today}-{count + 1:04d}"
        super().save(*args, **kwargs)

    def calculate_outstanding(self):
        """Recalculate outstanding balance."""
        self.outstanding_balance = self.total_repayment - self.amount_repaid
        if self.outstanding_balance <= 0:
            self.outstanding_balance = 0
            self.status = self.Status.PAID_OFF
            self.paid_off_date = timezone.now().date()
        self.save()


class LoanRepayment(BaseModel):
    """
    Individual repayment transactions.
    """

    class PaymentType(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled Payment"
        AUTO_DEDUCT = "auto_deduct", "Auto-Deduction"
        MANUAL = "manual", "Manual Payment"
        EARLY = "early", "Early Payment"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REVERSED = "reversed", "Reversed"

    loan = models.ForeignKey(
        Loan,
        on_delete=models.PROTECT,
        related_name="repayments",
    )

    # Payment details
    payment_number = models.CharField(max_length=50, unique=True)
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.SCHEDULED,
    )

    # Amounts
    amount_due = models.DecimalField(max_digits=10, decimal_places=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=0)
    principal_paid = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    interest_paid = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    late_fee_paid = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    # Dates
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    is_late = models.BooleanField(default=False)
    days_late = models.PositiveSmallIntegerField(default=0)

    # Balance after this payment
    balance_after = models.DecimalField(max_digits=12, decimal_places=0)

    # Payment method
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)

    # Source (for auto-deductions)
    source_order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loan_repayments",
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["due_date"]
        indexes = [
            models.Index(fields=["loan", "due_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment_number"]),
        ]

    def __str__(self):
        return f"{self.payment_number} - {self.amount_paid} XOF"

    def save(self, *args, **kwargs):
        if not self.payment_number:
            count = LoanRepayment.objects.filter(loan=self.loan).count()
            self.payment_number = f"{self.loan.loan_number}-P{count + 1:03d}"
        super().save(*args, **kwargs)


class FinancingSettings(BaseModel):
    """
    Global financing settings for the platform.
    """

    restaurant = models.OneToOneField(
        "authentication.Restaurant",
        on_delete=models.CASCADE,
        related_name="financing_settings",
    )

    # Opt-in
    financing_enabled = models.BooleanField(
        default=False,
        help_text="Restaurant has opted into financing features"
    )
    auto_deduct_consent = models.BooleanField(
        default=False,
        help_text="Consent to automatic deductions from sales"
    )

    # Preferences
    preferred_partner = models.ForeignKey(
        FinancePartner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    max_auto_deduct_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=15,
        help_text="Maximum percentage of daily sales for auto-deduction"
    )

    # Notifications
    notify_payment_due = models.BooleanField(default=True)
    notify_payment_processed = models.BooleanField(default=True)
    notify_new_offers = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Financing settings"

    def __str__(self):
        return f"Financing settings for {self.restaurant.name}"
