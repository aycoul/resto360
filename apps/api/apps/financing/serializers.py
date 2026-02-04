"""
Serializers for the Restaurant Financing API.
"""

from rest_framework import serializers

from .models import (
    CreditScore,
    FinancePartner,
    FinancingSettings,
    Loan,
    LoanApplication,
    LoanProduct,
    LoanRepayment,
)


class FinancePartnerSerializer(serializers.ModelSerializer):
    """Serializer for finance partners."""

    loan_products_count = serializers.SerializerMethodField()

    class Meta:
        model = FinancePartner
        fields = [
            "id",
            "name",
            "slug",
            "partner_type",
            "description",
            "email",
            "phone",
            "website",
            "logo",
            "min_loan_amount",
            "max_loan_amount",
            "min_interest_rate",
            "max_interest_rate",
            "min_term_months",
            "max_term_months",
            "min_credit_score",
            "min_platform_tenure_days",
            "min_monthly_revenue",
            "is_featured",
            "loan_products_count",
        ]

    def get_loan_products_count(self, obj):
        return obj.loan_products.filter(is_active=True).count()


class LoanProductSerializer(serializers.ModelSerializer):
    """Serializer for loan products."""

    partner_name = serializers.CharField(source="partner.name", read_only=True)

    class Meta:
        model = LoanProduct
        fields = [
            "id",
            "partner",
            "partner_name",
            "name",
            "product_type",
            "description",
            "min_amount",
            "max_amount",
            "interest_rate",
            "term_months",
            "origination_fee",
            "late_fee",
            "repayment_frequency",
            "auto_deduct",
            "auto_deduct_percentage",
            "min_credit_score",
            "min_monthly_revenue",
            "is_active",
        ]


class CreditScoreSerializer(serializers.ModelSerializer):
    """Serializer for credit scores."""

    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)

    class Meta:
        model = CreditScore
        fields = [
            "id",
            "restaurant",
            "restaurant_name",
            "score",
            "score_band",
            "revenue_score",
            "payment_score",
            "order_score",
            "tenure_score",
            "activity_score",
            "avg_monthly_revenue",
            "revenue_growth_rate",
            "avg_monthly_orders",
            "platform_tenure_days",
            "payment_success_rate",
            "active_days_ratio",
            "total_loans_taken",
            "loans_repaid_on_time",
            "loans_defaulted",
            "current_outstanding",
            "last_calculated",
        ]
        read_only_fields = fields


class CreditScoreSummarySerializer(serializers.ModelSerializer):
    """Simplified credit score for display."""

    class Meta:
        model = CreditScore
        fields = [
            "score",
            "score_band",
            "avg_monthly_revenue",
            "platform_tenure_days",
            "last_calculated",
        ]


class LoanApplicationListSerializer(serializers.ModelSerializer):
    """Serializer for listing loan applications."""

    partner_name = serializers.CharField(source="partner.name", read_only=True)

    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "application_number",
            "partner",
            "partner_name",
            "amount_requested",
            "term_months",
            "purpose",
            "status",
            "submitted_at",
            "created_at",
        ]


class LoanApplicationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for loan applications."""

    partner = FinancePartnerSerializer(read_only=True)
    loan_product = LoanProductSerializer(read_only=True)
    applicant_name = serializers.SerializerMethodField()

    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "application_number",
            "restaurant",
            "partner",
            "loan_product",
            "applicant_name",
            "amount_requested",
            "term_months",
            "purpose",
            "purpose_details",
            "status",
            "credit_score_at_application",
            "monthly_revenue_at_application",
            "amount_approved",
            "interest_rate_offered",
            "term_months_approved",
            "monthly_payment",
            "total_repayment",
            "submitted_at",
            "reviewed_at",
            "approved_at",
            "rejected_at",
            "disbursed_at",
            "review_notes",
            "rejection_reason",
            "documents",
            "created_at",
            "updated_at",
        ]

    def get_applicant_name(self, obj):
        if obj.applicant:
            return obj.applicant.get_full_name() or obj.applicant.phone_number
        return None


class CreateLoanApplicationSerializer(serializers.ModelSerializer):
    """Serializer for creating loan applications."""

    class Meta:
        model = LoanApplication
        fields = [
            "partner",
            "loan_product",
            "amount_requested",
            "term_months",
            "purpose",
            "purpose_details",
            "documents",
        ]

    def validate(self, data):
        # Check loan product belongs to partner
        if data.get("loan_product") and data.get("partner"):
            if data["loan_product"].partner != data["partner"]:
                raise serializers.ValidationError(
                    "Loan product does not belong to selected partner"
                )
        return data


class SubmitApplicationSerializer(serializers.Serializer):
    """Serializer for submitting an application."""

    confirm = serializers.BooleanField()


class LoanListSerializer(serializers.ModelSerializer):
    """Serializer for listing loans."""

    partner_name = serializers.CharField(source="partner.name", read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            "id",
            "loan_number",
            "partner",
            "partner_name",
            "principal",
            "outstanding_balance",
            "next_payment_date",
            "next_payment_amount",
            "status",
            "progress_percentage",
            "disbursement_date",
            "maturity_date",
        ]

    def get_progress_percentage(self, obj):
        if obj.total_repayment > 0:
            return round((float(obj.amount_repaid) / float(obj.total_repayment)) * 100, 1)
        return 0


class LoanDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for loans."""

    partner = FinancePartnerSerializer(read_only=True)
    recent_repayments = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            "id",
            "loan_number",
            "application",
            "partner",
            "principal",
            "interest_rate",
            "term_months",
            "origination_fee",
            "total_interest",
            "total_repayment",
            "monthly_payment",
            "amount_disbursed",
            "amount_repaid",
            "outstanding_balance",
            "next_payment_date",
            "next_payment_amount",
            "auto_deduct_enabled",
            "auto_deduct_percentage",
            "disbursement_date",
            "first_payment_date",
            "maturity_date",
            "paid_off_date",
            "status",
            "days_overdue",
            "missed_payments",
            "progress_percentage",
            "recent_repayments",
            "created_at",
        ]

    def get_progress_percentage(self, obj):
        if obj.total_repayment > 0:
            return round((float(obj.amount_repaid) / float(obj.total_repayment)) * 100, 1)
        return 0

    def get_recent_repayments(self, obj):
        repayments = obj.repayments.order_by("-due_date")[:5]
        return LoanRepaymentSerializer(repayments, many=True).data


class LoanRepaymentSerializer(serializers.ModelSerializer):
    """Serializer for loan repayments."""

    class Meta:
        model = LoanRepayment
        fields = [
            "id",
            "payment_number",
            "payment_type",
            "amount_due",
            "amount_paid",
            "principal_paid",
            "interest_paid",
            "late_fee_paid",
            "due_date",
            "payment_date",
            "status",
            "is_late",
            "days_late",
            "balance_after",
            "payment_method",
            "payment_reference",
        ]


class MakePaymentSerializer(serializers.Serializer):
    """Serializer for making a manual payment."""

    amount = serializers.DecimalField(max_digits=10, decimal_places=0)
    payment_method = serializers.CharField(max_length=50)
    payment_reference = serializers.CharField(max_length=100, required=False)


class FinancingSettingsSerializer(serializers.ModelSerializer):
    """Serializer for financing settings."""

    class Meta:
        model = FinancingSettings
        fields = [
            "id",
            "financing_enabled",
            "auto_deduct_consent",
            "preferred_partner",
            "max_auto_deduct_percentage",
            "notify_payment_due",
            "notify_payment_processed",
            "notify_new_offers",
        ]


class FinancingDashboardSerializer(serializers.Serializer):
    """Serializer for financing dashboard overview."""

    credit_score = CreditScoreSummarySerializer()
    active_loans_count = serializers.IntegerField()
    total_outstanding = serializers.DecimalField(max_digits=14, decimal_places=0)
    next_payment_date = serializers.DateField(allow_null=True)
    next_payment_amount = serializers.DecimalField(
        max_digits=10, decimal_places=0, allow_null=True
    )
    pending_applications = serializers.IntegerField()
    available_credit = serializers.DecimalField(max_digits=14, decimal_places=0)
    eligible_partners = serializers.IntegerField()


class LoanEligibilitySerializer(serializers.Serializer):
    """Serializer for loan eligibility check."""

    eligible = serializers.BooleanField()
    max_amount = serializers.DecimalField(max_digits=12, decimal_places=0)
    reasons = serializers.ListField(child=serializers.CharField())
    suggestions = serializers.ListField(child=serializers.CharField())
    eligible_products = LoanProductSerializer(many=True)


class LoanCalculatorSerializer(serializers.Serializer):
    """Serializer for loan calculator input."""

    amount = serializers.DecimalField(max_digits=12, decimal_places=0)
    term_months = serializers.IntegerField(min_value=1, max_value=60)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class LoanCalculatorResultSerializer(serializers.Serializer):
    """Serializer for loan calculator output."""

    principal = serializers.DecimalField(max_digits=12, decimal_places=0)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    term_months = serializers.IntegerField()
    monthly_payment = serializers.DecimalField(max_digits=10, decimal_places=0)
    total_interest = serializers.DecimalField(max_digits=12, decimal_places=0)
    total_repayment = serializers.DecimalField(max_digits=12, decimal_places=0)
    schedule = serializers.ListField(child=serializers.DictField())
