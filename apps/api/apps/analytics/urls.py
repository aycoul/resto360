"""
URL configuration for analytics API.
"""
from django.urls import path

from .views import AnalyticsSummaryAPI, TrackMenuViewAPI

urlpatterns = [
    path("track/", TrackMenuViewAPI.as_view(), name="analytics-track"),
    path("summary/", AnalyticsSummaryAPI.as_view(), name="analytics-summary"),
]
