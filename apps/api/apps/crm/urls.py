"""
CRM & Loyalty URL Configuration
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"customers", views.CustomerViewSet, basename="customer")
router.register(r"tiers", views.LoyaltyTierViewSet, basename="tier")
router.register(r"rewards", views.LoyaltyRewardViewSet, basename="reward")
router.register(r"campaigns", views.CampaignViewSet, basename="campaign")
router.register(r"redemptions", views.RewardRedemptionViewSet, basename="redemption")

urlpatterns = [
    path("", include(router.urls)),
    path("summary/", views.CRMSummaryView.as_view(), name="crm-summary"),
    path("program/", views.LoyaltyProgramView.as_view(), name="loyalty-program"),
    path("validate-code/", views.ValidateRedemptionCodeView.as_view(), name="validate-code"),
]
