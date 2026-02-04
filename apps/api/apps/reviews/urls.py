"""URL configuration for reviews app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FeedbackRequestViewSet,
    PublicReviewsView,
    PublicSubmitReviewView,
    ReviewSettingsView,
    ReviewSummaryView,
    ReviewViewSet,
    SubmitFeedbackView,
)

router = DefaultRouter()
router.register("reviews", ReviewViewSet, basename="review")
router.register("feedback-requests", FeedbackRequestViewSet, basename="feedback-request")

urlpatterns = [
    # Settings and summary
    path("settings/", ReviewSettingsView.as_view(), name="review-settings"),
    path("summary/", ReviewSummaryView.as_view(), name="review-summary"),

    # Public endpoints
    path("public/<slug:slug>/", PublicReviewsView.as_view(), name="public-reviews"),
    path("public/<slug:slug>/submit/", PublicSubmitReviewView.as_view(), name="public-submit-review"),

    # Feedback submission via token
    path("feedback/<str:token>/", SubmitFeedbackView.as_view(), name="submit-feedback"),

    # Router URLs
    path("", include(router.urls)),
]
