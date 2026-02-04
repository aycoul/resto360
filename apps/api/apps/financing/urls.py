"""
URL configuration for the Restaurant Financing API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CreditScoreAPI,
    FinancePartnerViewSet,
    FinancingDashboardAPI,
    FinancingSettingsAPI,
    LoanApplicationViewSet,
    LoanCalculatorAPI,
    LoanEligibilityAPI,
    LoanProductViewSet,
    LoanViewSet,
)

router = DefaultRouter()
router.register(r"partners", FinancePartnerViewSet, basename="finance-partner")
router.register(r"products", LoanProductViewSet, basename="loan-product")
router.register(r"applications", LoanApplicationViewSet, basename="loan-application")
router.register(r"loans", LoanViewSet, basename="loan")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", FinancingDashboardAPI.as_view(), name="financing-dashboard"),
    path("credit-score/", CreditScoreAPI.as_view(), name="credit-score"),
    path("eligibility/", LoanEligibilityAPI.as_view(), name="loan-eligibility"),
    path("calculator/", LoanCalculatorAPI.as_view(), name="loan-calculator"),
    path("settings/", FinancingSettingsAPI.as_view(), name="financing-settings"),
]
