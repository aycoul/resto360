"""
URL configuration for analytics API.
"""
from django.urls import path

from .views import (
    AdvancedDashboardAPI,
    AnalyticsSummaryAPI,
    BenchmarkAPI,
    CategoryPerformanceAPI,
    CustomerAnalyticsAPI,
    ExportReportAPI,
    ItemPerformanceAPI,
    PeakHoursAPI,
    SalesStatsAPI,
    TrackMenuViewAPI,
    WeeklyReportsAPI,
)

urlpatterns = [
    # Basic analytics
    path("track/", TrackMenuViewAPI.as_view(), name="analytics-track"),
    path("summary/", AnalyticsSummaryAPI.as_view(), name="analytics-summary"),

    # Advanced analytics
    path("dashboard/", AdvancedDashboardAPI.as_view(), name="analytics-dashboard"),
    path("sales/", SalesStatsAPI.as_view(), name="analytics-sales"),
    path("items/", ItemPerformanceAPI.as_view(), name="analytics-items"),
    path("categories/", CategoryPerformanceAPI.as_view(), name="analytics-categories"),
    path("peak-hours/", PeakHoursAPI.as_view(), name="analytics-peak-hours"),
    path("customers/", CustomerAnalyticsAPI.as_view(), name="analytics-customers"),
    path("weekly-reports/", WeeklyReportsAPI.as_view(), name="analytics-weekly-reports"),
    path("export/", ExportReportAPI.as_view(), name="analytics-export"),
    path("benchmarks/", BenchmarkAPI.as_view(), name="analytics-benchmarks"),
]
