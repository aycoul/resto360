"""
Admin configuration for the Restaurant Financing app.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    CreditScore,
    FinancePartner,
    FinancingSettings,
    Loan,
    LoanApplication,
    LoanProduct,
    LoanRepayment,
)


class LoanProductInline(admin.TabularInline):
    model = LoanProduct
    extra = 0
    fields = [
        "name",
        "product_type",
        "interest_rate",
        "min_amount",
        "max_amount",
        "term_months",
        "is_active",
    ]


@admin.register(FinancePartner)
class FinancePartnerAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "partner_type",
        "min_loan_amount",
        "max_loan_amount",
        "min_interest_rate",
        "max_interest_rate",
        "is_active",
        "is_featured",
    ]
    list_filter = ["partner_type", "is_active", "is_featured"]
    search_fields = ["name", "slug", "description"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [LoanProductInline]
    fieldsets = [
        (None, {"fields": ["name", "slug", "partner_type", "description", "logo"]}),
        ("Contact", {"fields": ["email", "phone", "website"]}),
        (
            "Loan Parameters",
            {
                "fields": [
                    ("min_loan_amount", "max_loan_amount"),
                    ("min_interest_rate", "max_interest_rate"),
                    ("min_term_months", "max_term_months"),
                ]
            },
        ),
        (
            "Eligibility",
            {
                "fields": [
                    "min_credit_score",
                    "min_platform_tenure_days",
                    "min_monthly_revenue",
                ]
            },
        ),
        ("API Integration", {"fields": ["api_endpoint", "api_key"], "classes": ["collapse"]}),
        ("Status", {"fields": ["is_active", "is_featured"]}),
    ]


@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "partner",
        "product_type",
        "interest_rate",
        "term_months",
        "min_amount",
        "max_amount",
        "is_active",
    ]
    list_filter = ["partner", "product_type", "repayment_frequency", "is_active"]
    search_fields = ["name", "partner__name", "description"]
    autocomplete_fields = ["partner"]


@admin.register(CreditScore)
class CreditScoreAdmin(admin.ModelAdmin):
    list_display = [
        "business",
        "score_display",
        "score_band",
        "avg_monthly_revenue",
        "platform_tenure_days",
        "last_calculated",
    ]
    list_filter = ["score_band"]
    search_fields = ["business__name"]
    readonly_fields = [
        "score",
        "score_band",
        "revenue_score",
        "payment_score",
        "order_score",
        "tenure_score",
        "activity_score",
        "last_calculated",
    ]

    def score_display(self, obj):
        """Display score with color coding."""
        if obj.score >= 700:
            color = "green"
        elif obj.score >= 500:
            color = "orange"
        else:
            color = "red"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.score,
        )

    score_display.short_description = "Score"


class LoanRepaymentInline(admin.TabularInline):
    model = LoanRepayment
    extra = 0
    fields = [
        "payment_number",
        "payment_type",
        "amount_due",
        "amount_paid",
        "due_date",
        "payment_date",
        "status",
    ]
    readonly_fields = ["payment_number"]


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "application_number",
        "business",
        "partner",
        "amount_requested",
        "term_months",
        "status",
        "submitted_at",
        "created_at",
    ]
    list_filter = ["status", "partner", "purpose"]
    search_fields = ["application_number", "business__name", "partner__name"]
    autocomplete_fields = ["business", "partner", "loan_product"]
    readonly_fields = [
        "application_number",
        "credit_score_at_application",
        "monthly_revenue_at_application",
        "submitted_at",
        "reviewed_at",
        "approved_at",
        "rejected_at",
        "disbursed_at",
    ]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "application_number",
                    "business",
                    "applicant",
                    "partner",
                    "loan_product",
                ]
            },
        ),
        (
            "Request",
            {
                "fields": [
                    "amount_requested",
                    "term_months",
                    "purpose",
                    "purpose_details",
                ]
            },
        ),
        (
            "Approval",
            {
                "fields": [
                    "amount_approved",
                    "interest_rate_offered",
                    "term_months_approved",
                    "monthly_payment",
                    "total_repayment",
                ]
            },
        ),
        (
            "Status",
            {
                "fields": [
                    "status",
                    "credit_score_at_application",
                    "monthly_revenue_at_application",
                    "review_notes",
                    "rejection_reason",
                ]
            },
        ),
        (
            "Timeline",
            {
                "fields": [
                    "submitted_at",
                    "reviewed_at",
                    "approved_at",
                    "rejected_at",
                    "disbursed_at",
                ]
            },
        ),
        ("Documents", {"fields": ["documents"], "classes": ["collapse"]}),
    ]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = [
        "loan_number",
        "business",
        "partner",
        "principal",
        "outstanding_balance",
        "status",
        "next_payment_date",
        "disbursement_date",
    ]
    list_filter = ["status", "partner", "auto_deduct_enabled"]
    search_fields = ["loan_number", "business__name", "partner__name"]
    autocomplete_fields = ["business", "partner", "application"]
    readonly_fields = [
        "loan_number",
        "total_interest",
        "total_repayment",
        "outstanding_balance",
        "days_overdue",
        "missed_payments",
    ]
    inlines = [LoanRepaymentInline]
    fieldsets = [
        (None, {"fields": ["loan_number", "application", "business", "partner"]}),
        (
            "Loan Terms",
            {
                "fields": [
                    "principal",
                    "interest_rate",
                    "term_months",
                    "origination_fee",
                    ("total_interest", "total_repayment"),
                    "monthly_payment",
                ]
            },
        ),
        (
            "Repayment",
            {
                "fields": [
                    "amount_disbursed",
                    "amount_repaid",
                    "outstanding_balance",
                    ("next_payment_date", "next_payment_amount"),
                ]
            },
        ),
        (
            "Auto-Deduction",
            {"fields": ["auto_deduct_enabled", "auto_deduct_percentage"]},
        ),
        (
            "Timeline",
            {
                "fields": [
                    "disbursement_date",
                    "first_payment_date",
                    "maturity_date",
                    "paid_off_date",
                ]
            },
        ),
        (
            "Status",
            {"fields": ["status", "days_overdue", "missed_payments"]},
        ),
    ]


@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = [
        "loan",
        "payment_number",
        "payment_type",
        "amount_due",
        "amount_paid",
        "due_date",
        "payment_date",
        "status",
    ]
    list_filter = ["status", "payment_type", "is_late"]
    search_fields = ["loan__loan_number", "loan__business__name", "payment_reference"]
    autocomplete_fields = ["loan"]
    readonly_fields = ["payment_number", "balance_after"]


@admin.register(FinancingSettings)
class FinancingSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "business",
        "financing_enabled",
        "auto_deduct_consent",
        "max_auto_deduct_percentage",
    ]
    list_filter = ["financing_enabled", "auto_deduct_consent"]
    search_fields = ["business__name"]
    autocomplete_fields = ["business", "preferred_partner"]
