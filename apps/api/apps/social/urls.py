"""
Social Media Automation URL Configuration
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AICaptionViewSet,
    ConnectAccountView,
    ContentCalendarViewSet,
    PostTemplateViewSet,
    SocialAccountViewSet,
    SocialAnalyticsView,
    SocialDashboardView,
    SocialPostViewSet,
)

router = DefaultRouter()
router.register(r"accounts", SocialAccountViewSet, basename="social-account")
router.register(r"templates", PostTemplateViewSet, basename="post-template")
router.register(r"posts", SocialPostViewSet, basename="social-post")
router.register(r"calendar", ContentCalendarViewSet, basename="content-calendar")
router.register(r"captions", AICaptionViewSet, basename="ai-caption")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", SocialDashboardView.as_view(), name="social-dashboard"),
    path("analytics/", SocialAnalyticsView.as_view(), name="social-analytics"),
    path("connect/", ConnectAccountView.as_view(), name="connect-account"),
]
