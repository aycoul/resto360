"""
Views for the Restaurant Financing API.
"""

from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    CreditScore,
    FinancePartner,
    FinancingSettings,
    Loan,
    LoanApplication,
    LoanProduct,
    LoanRepayment,
)
from .serializers import (
    CreateLoanApplicationSerializer,
    CreditScoreSerializer,
    FinancePartnerSerializer,
    FinancingDashboardSerializer,
    FinancingSettingsSerializer,
    LoanApplicationDetailSerializer,
    LoanApplicationListSerializer,
    LoanCalculatorResultSerializer,
    LoanCalculatorSerializer,
    LoanDetailSerializer,
    LoanEligibilitySerializer,
    LoanListSerializer,
    LoanProductSerializer,
    LoanRepaymentSerializer,
    MakePaymentSerializer,
    SubmitApplicationSerializer,
)


class FinancePartnerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing finance partners.
    """

    queryset = FinancePartner.objects.filter(is_active=True)
    serializer_class = FinancePartnerSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by partner type
        partner_type = self.request.query_params.get("type")
        if partner_type:
            queryset = queryset.filter(partner_type=partner_type)

        return queryset

    @action(detail=True, methods=["get"])
    def products(self, request, slug=None):
        """Get loan products offered by this partner."""
        partner = self.get_object()
        products = partner.loan_products.filter(is_active=True)
        serializer = LoanProductSerializer(products, many=True)
        return Response(serializer.data)


class LoanProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing loan products.
    """

    queryset = LoanProduct.objects.filter(is_active=True, partner__is_active=True)
    serializer_class = LoanProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by product type
        product_type = self.request.query_params.get("type")
        if product_type:
            queryset = queryset.filter(product_type=product_type)

        # Filter by partner
        partner = self.request.query_params.get("partner")
        if partner:
            queryset = queryset.filter(partner__slug=partner)

        return queryset


class CreditScoreAPI(APIView):
    """
    API for viewing and refreshing credit score.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get current credit score."""
        restaurant = getattr(request.user, "restaurant", None)
        if not restaurant:
            return Response(
                {"error": "No restaurant associated with this user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        credit_score, created = CreditScore.objects.get_or_create(
            restaurant=restaurant
        )

        # If new or stale, calculate
        if created or (timezone.now() - credit_score.last_calculated).days > 1:
            self._calculate_score(credit_score, restaurant)

        serializer = CreditScoreSerializer(credit_score)
        return Response(serializer.data)

    def post(self, request):
        """Refresh credit score."""
        restaurant = getattr(request.user, "restaurant", None)
        if not restaurant:
            return Response(
                {"error": "No restaurant associated with this user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        credit_score, _ = CreditScore.objects.get_or_create(restaurant=restaurant)
        self._calculate_score(credit_score, restaurant)

        serializer = CreditScoreSerializer(credit_score)
        return Response(serializer.data)

    def _calculate_score(self, credit_score, restaurant):
        """Calculate credit score from restaurant data."""
        # This would normally aggregate real data from orders, payments, etc.
        # For now, we'll use mock calculations

        # Calculate platform tenure
        tenure_days = (timezone.now() - restaurant.created_at).days
        credit_score.platform_tenure_days = tenure_days

        # Tenure score (0-100)
        if tenure_days >= 365:
            credit_score.tenure_score = 100
        elif tenure_days >= 180:
            credit_score.tenure_score = 80
        elif tenure_days >= 90:
            credit_score.tenure_score = 60
        elif tenure_days >= 30:
            credit_score.tenure_score = 40
        else:
            credit_score.tenure_score = 20

        # Mock other scores (in production, calculate from real data)
        credit_score.revenue_score = 70
        credit_score.payment_score = 85
        credit_score.order_score = 75
        credit_score.activity_score = 80

        # Mock metrics
        credit_score.avg_monthly_revenue = 1500000
        credit_score.revenue_growth_rate = Decimal("5.5")
        credit_score.avg_monthly_orders = 450
        credit_score.payment_success_rate = Decimal("98.5")
        credit_score.active_days_ratio = Decimal("92.0")

        # Calculate overall score
        credit_score.calculate_score()


class LoanApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for loan applications.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateLoanApplicationSerializer
        if self.action == "retrieve":
            return LoanApplicationDetailSerializer
        return LoanApplicationListSerializer

    def get_queryset(self):
        restaurant = getattr(self.request.user, "restaurant", None)
        if not restaurant:
            return LoanApplication.objects.none()
        return LoanApplication.objects.filter(restaurant=restaurant)

    def perform_create(self, serializer):
        restaurant = getattr(self.request.user, "restaurant", None)
        if not restaurant:
            raise serializers.ValidationError("No restaurant associated with this user")

        # Get credit score
        credit_score = CreditScore.objects.filter(restaurant=restaurant).first()
        credit_score_value = credit_score.score if credit_score else 0
        monthly_revenue = credit_score.avg_monthly_revenue if credit_score else 0

        serializer.save(
            restaurant=restaurant,
            applicant=self.request.user,
            credit_score_at_application=credit_score_value,
            monthly_revenue_at_application=monthly_revenue,
            status=LoanApplication.Status.DRAFT,
        )

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Submit application for review."""
        application = self.get_object()

        if application.status != LoanApplication.Status.DRAFT:
            return Response(
                {"error": "Application has already been submitted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SubmitApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["confirm"]:
            application.status = LoanApplication.Status.SUBMITTED
            application.submitted_at = timezone.now()
            application.save()

            return Response(LoanApplicationDetailSerializer(application).data)

        return Response({"error": "Confirmation required"}, status=400)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel application."""
        application = self.get_object()

        if application.status in [
            LoanApplication.Status.APPROVED,
            LoanApplication.Status.DISBURSED,
        ]:
            return Response(
                {"error": "Cannot cancel approved or disbursed applications"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application.status = LoanApplication.Status.CANCELLED
        application.save()

        return Response(LoanApplicationDetailSerializer(application).data)


class LoanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for loans.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LoanDetailSerializer
        return LoanListSerializer

    def get_queryset(self):
        restaurant = getattr(self.request.user, "restaurant", None)
        if not restaurant:
            return Loan.objects.none()
        return Loan.objects.filter(restaurant=restaurant)

    @action(detail=True, methods=["get"])
    def repayments(self, request, pk=None):
        """Get all repayments for this loan."""
        loan = self.get_object()
        repayments = loan.repayments.all()
        serializer = LoanRepaymentSerializer(repayments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def make_payment(self, request, pk=None):
        """Make a manual payment on this loan."""
        loan = self.get_object()

        if loan.status != Loan.Status.ACTIVE:
            return Response(
                {"error": "Loan is not active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MakePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        if amount > loan.outstanding_balance:
            amount = loan.outstanding_balance

        # Create repayment record
        repayment = LoanRepayment.objects.create(
            loan=loan,
            payment_type=LoanRepayment.PaymentType.MANUAL,
            amount_due=loan.next_payment_amount,
            amount_paid=amount,
            due_date=loan.next_payment_date,
            payment_date=timezone.now().date(),
            status=LoanRepayment.Status.COMPLETED,
            balance_after=loan.outstanding_balance - amount,
            payment_method=serializer.validated_data["payment_method"],
            payment_reference=serializer.validated_data.get("payment_reference", ""),
        )

        # Update loan
        loan.amount_repaid += amount
        loan.calculate_outstanding()

        return Response(LoanRepaymentSerializer(repayment).data)

    @action(detail=True, methods=["post"])
    def toggle_auto_deduct(self, request, pk=None):
        """Toggle auto-deduction for this loan."""
        loan = self.get_object()
        loan.auto_deduct_enabled = not loan.auto_deduct_enabled
        loan.save()

        return Response({
            "auto_deduct_enabled": loan.auto_deduct_enabled,
            "message": "Auto-deduction enabled" if loan.auto_deduct_enabled else "Auto-deduction disabled"
        })


class FinancingDashboardAPI(APIView):
    """
    Dashboard overview for financing.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        restaurant = getattr(request.user, "restaurant", None)
        if not restaurant:
            return Response(
                {"error": "No restaurant associated with this user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get credit score
        credit_score = CreditScore.objects.filter(restaurant=restaurant).first()

        # Get active loans
        active_loans = Loan.objects.filter(
            restaurant=restaurant,
            status=Loan.Status.ACTIVE,
        )

        # Calculate totals
        total_outstanding = active_loans.aggregate(
            total=Sum("outstanding_balance")
        )["total"] or 0

        # Get next payment
        next_loan = active_loans.order_by("next_payment_date").first()

        # Pending applications
        pending_apps = LoanApplication.objects.filter(
            restaurant=restaurant,
            status__in=[
                LoanApplication.Status.SUBMITTED,
                LoanApplication.Status.UNDER_REVIEW,
            ],
        ).count()

        # Eligible partners (simplified check)
        eligible_partners = FinancePartner.objects.filter(
            is_active=True,
            min_credit_score__lte=credit_score.score if credit_score else 0,
        ).count()

        # Available credit (simplified calculation)
        available_credit = 0
        if credit_score and credit_score.avg_monthly_revenue > 0:
            # Available credit = 3x monthly revenue minus outstanding
            available_credit = max(
                0,
                (credit_score.avg_monthly_revenue * 3) - total_outstanding
            )

        data = {
            "credit_score": credit_score,
            "active_loans_count": active_loans.count(),
            "total_outstanding": total_outstanding,
            "next_payment_date": next_loan.next_payment_date if next_loan else None,
            "next_payment_amount": next_loan.next_payment_amount if next_loan else None,
            "pending_applications": pending_apps,
            "available_credit": available_credit,
            "eligible_partners": eligible_partners,
        }

        serializer = FinancingDashboardSerializer(data)
        return Response(serializer.data)


class LoanEligibilityAPI(APIView):
    """
    Check loan eligibility.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        restaurant = getattr(request.user, "restaurant", None)
        if not restaurant:
            return Response(
                {"error": "No restaurant associated with this user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        credit_score = CreditScore.objects.filter(restaurant=restaurant).first()

        if not credit_score:
            return Response({
                "eligible": False,
                "max_amount": 0,
                "reasons": ["Credit score not calculated yet"],
                "suggestions": ["Wait for credit score calculation"],
                "eligible_products": [],
            })

        reasons = []
        suggestions = []
        eligible = True

        # Check credit score
        if credit_score.score < 400:
            eligible = False
            reasons.append("Credit score too low")
            suggestions.append("Improve your credit score by maintaining consistent sales")

        # Check platform tenure
        if credit_score.platform_tenure_days < 30:
            eligible = False
            reasons.append("Platform tenure too short")
            suggestions.append(f"Wait {30 - credit_score.platform_tenure_days} more days")

        # Check existing defaults
        if credit_score.loans_defaulted > 0:
            eligible = False
            reasons.append("Previous loan defaults on record")
            suggestions.append("Contact support to discuss your situation")

        # Calculate max amount
        max_amount = 0
        if eligible:
            max_amount = min(
                credit_score.avg_monthly_revenue * 3,
                Decimal("10000000")  # Cap at 10 million XOF
            )

        # Get eligible products
        eligible_products = []
        if eligible:
            eligible_products = LoanProduct.objects.filter(
                is_active=True,
                partner__is_active=True,
                min_credit_score__lte=credit_score.score,
            )

        if eligible and not reasons:
            reasons = ["You are eligible for financing"]

        serializer = LoanEligibilitySerializer({
            "eligible": eligible,
            "max_amount": max_amount,
            "reasons": reasons,
            "suggestions": suggestions,
            "eligible_products": eligible_products,
        })

        return Response(serializer.data)


class LoanCalculatorAPI(APIView):
    """
    Loan calculator.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoanCalculatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        term_months = serializer.validated_data["term_months"]
        annual_rate = serializer.validated_data["interest_rate"]

        # Calculate monthly rate
        monthly_rate = annual_rate / 100 / 12

        # Calculate monthly payment using amortization formula
        if monthly_rate > 0:
            monthly_payment = amount * (
                monthly_rate * (1 + monthly_rate) ** term_months
            ) / ((1 + monthly_rate) ** term_months - 1)
        else:
            monthly_payment = amount / term_months

        total_repayment = monthly_payment * term_months
        total_interest = total_repayment - amount

        # Generate schedule
        schedule = []
        balance = float(amount)
        for month in range(1, term_months + 1):
            interest_payment = balance * float(monthly_rate)
            principal_payment = float(monthly_payment) - interest_payment
            balance -= principal_payment

            schedule.append({
                "month": month,
                "payment": round(monthly_payment),
                "principal": round(principal_payment),
                "interest": round(interest_payment),
                "balance": max(0, round(balance)),
            })

        result = {
            "principal": amount,
            "interest_rate": annual_rate,
            "term_months": term_months,
            "monthly_payment": round(monthly_payment),
            "total_interest": round(total_interest),
            "total_repayment": round(total_repayment),
            "schedule": schedule,
        }

        return Response(LoanCalculatorResultSerializer(result).data)


class FinancingSettingsAPI(APIView):
    """
    Financing settings for a restaurant.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        restaurant = getattr(request.user, "restaurant", None)
        if not restaurant:
            return Response(
                {"error": "No restaurant associated with this user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        settings, _ = FinancingSettings.objects.get_or_create(
            restaurant=restaurant
        )
        serializer = FinancingSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        restaurant = getattr(request.user, "restaurant", None)
        if not restaurant:
            return Response(
                {"error": "No restaurant associated with this user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        settings, _ = FinancingSettings.objects.get_or_create(
            restaurant=restaurant
        )

        serializer = FinancingSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
