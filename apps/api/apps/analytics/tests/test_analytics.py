"""
Tests for analytics API endpoints and services.
"""
import uuid

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import Restaurant, User

from ..models import DailyMenuStats, MenuView
from ..services import aggregate_daily_stats, get_analytics_summary, track_menu_view


class AnalyticsModelsTest(TestCase):
    """Tests for analytics models."""

    def setUp(self):
        self.business = Restaurant.objects.create(
            name="Test Restaurant",
            slug="test-restaurant",
            phone="+2250700000001",
        )

    def test_menu_view_creation(self):
        """Test creating a MenuView record."""
        view = MenuView.all_objects.create(
            business=self.business,
            session_id="test-session-123",
            source="qr",
            user_agent="Mozilla/5.0 Test",
        )

        self.assertIsNotNone(view.id)
        self.assertEqual(view.business, self.business)
        self.assertEqual(view.session_id, "test-session-123")
        self.assertEqual(view.source, "qr")
        self.assertEqual(view.user_agent, "Mozilla/5.0 Test")
        self.assertIsNotNone(view.viewed_at)

    def test_daily_menu_stats_creation(self):
        """Test creating DailyMenuStats record."""
        from datetime import date

        stats = DailyMenuStats.all_objects.create(
            business=self.business,
            date=date.today(),
            total_views=100,
            unique_visitors=50,
            qr_scans=25,
        )

        self.assertIsNotNone(stats.id)
        self.assertEqual(stats.total_views, 100)
        self.assertEqual(stats.unique_visitors, 50)
        self.assertEqual(stats.qr_scans, 25)


class AnalyticsServicesTest(TestCase):
    """Tests for analytics service functions."""

    def setUp(self):
        self.business = Restaurant.objects.create(
            name="Test Restaurant",
            slug="test-restaurant",
            phone="+2250700000002",
        )

    def test_track_menu_view(self):
        """Test tracking a menu view."""
        view = track_menu_view(
            business=self.business,
            session_id="session-abc",
            source="qr",
            user_agent="Test Agent",
        )

        self.assertIsNotNone(view.id)
        self.assertEqual(view.business, self.business)
        self.assertEqual(view.session_id, "session-abc")
        self.assertEqual(view.source, "qr")

    def test_track_menu_view_invalid_source(self):
        """Test that invalid source defaults to 'other'."""
        view = track_menu_view(
            business=self.business,
            session_id="session-xyz",
            source="invalid",
            user_agent="Test Agent",
        )

        self.assertEqual(view.source, "other")

    def test_track_menu_view_truncates_user_agent(self):
        """Test that long user agent is truncated."""
        long_agent = "A" * 600  # Longer than 500 char limit

        view = track_menu_view(
            business=self.business,
            session_id="session-long",
            source="link",
            user_agent=long_agent,
        )

        self.assertEqual(len(view.user_agent), 500)

    def test_get_analytics_summary(self):
        """Test getting analytics summary."""
        # Create some test views
        for i in range(5):
            track_menu_view(
                business=self.business,
                session_id=f"session-{i}",
                source="link",
            )

        # Create a duplicate session to test unique count
        track_menu_view(
            business=self.business,
            session_id="session-0",
            source="qr",
        )

        summary = get_analytics_summary(self.business)

        self.assertEqual(summary["views_today"], 6)
        self.assertEqual(summary["unique_today"], 5)  # Only 5 unique sessions
        self.assertEqual(summary["views_week"], 6)
        self.assertEqual(summary["views_month"], 6)
        self.assertEqual(summary["menu_items"], 0)  # No menu items yet

    def test_aggregate_daily_stats(self):
        """Test daily stats aggregation."""
        # Create test views
        for i in range(3):
            track_menu_view(
                business=self.business,
                session_id=f"session-{i}",
                source="qr" if i == 0 else "link",
            )

        stats = aggregate_daily_stats(self.business)

        self.assertEqual(stats.total_views, 3)
        self.assertEqual(stats.unique_visitors, 3)
        self.assertEqual(stats.qr_scans, 1)


class TrackMenuViewAPITest(APITestCase):
    """Tests for the public tracking endpoint."""

    def setUp(self):
        self.business = Restaurant.objects.create(
            name="Test Restaurant",
            slug="test-restaurant",
            phone="+2250700000003",
            is_active=True,
        )
        self.track_url = reverse("analytics-track")

    def test_track_menu_view_public(self):
        """Test tracking view without authentication."""
        data = {
            "restaurant_slug": "test-restaurant",
            "session_id": str(uuid.uuid4()),
            "source": "qr",
            "user_agent": "Test Browser",
        }

        response = self.client.post(self.track_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "tracked")

        # Verify view was recorded
        self.assertEqual(MenuView.all_objects.count(), 1)
        view = MenuView.all_objects.first()
        self.assertEqual(view.source, "qr")

    def test_track_menu_view_nonexistent_business(self):
        """Test tracking view for non-existent business."""
        data = {
            "restaurant_slug": "nonexistent-slug",
            "session_id": str(uuid.uuid4()),
            "source": "link",
        }

        response = self.client.post(self.track_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(MenuView.all_objects.count(), 0)

    def test_track_menu_view_inactive_business(self):
        """Test tracking view for inactive business."""
        self.business.is_active = False
        self.business.save()

        data = {
            "restaurant_slug": "test-restaurant",
            "session_id": str(uuid.uuid4()),
            "source": "link",
        }

        response = self.client.post(self.track_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_track_menu_view_missing_fields(self):
        """Test tracking with missing required fields."""
        data = {
            "restaurant_slug": "test-restaurant",
            # Missing session_id
        }

        response = self.client.post(self.track_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AnalyticsSummaryAPITest(APITestCase):
    """Tests for the authenticated summary endpoint."""

    def setUp(self):
        self.business = Restaurant.objects.create(
            name="Test Restaurant",
            slug="test-restaurant",
            phone="+2250700000004",
            is_active=True,
        )
        self.user = User.objects.create_user(
            phone="+2250700000005",
            password="testpass123",
            name="Test Owner",
            business=self.business,
            role="owner",
        )
        self.summary_url = reverse("analytics-summary")

    def get_auth_header(self):
        """Get JWT auth header for test user."""
        refresh = RefreshToken.for_user(self.user)
        return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

    def test_analytics_summary_authenticated(self):
        """Test getting analytics summary with authentication."""
        # Create some views
        for i in range(3):
            track_menu_view(
                business=self.business,
                session_id=f"session-{i}",
                source="link",
            )

        response = self.client.get(self.summary_url, **self.get_auth_header())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["views_today"], 3)
        self.assertEqual(response.data["unique_today"], 3)
        self.assertIn("views_week", response.data)
        self.assertIn("views_month", response.data)
        self.assertIn("menu_items", response.data)

    def test_analytics_summary_unauthenticated(self):
        """Test that summary endpoint requires authentication."""
        response = self.client.get(self.summary_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_analytics_summary_no_business(self):
        """Test summary for user without business."""
        # Create user without business
        user_no_business = User.objects.create_user(
            phone="+2250700000006",
            password="testpass123",
            name="No Business User",
        )
        refresh = RefreshToken.for_user(user_no_business)
        auth_header = {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

        response = self.client.get(self.summary_url, **auth_header)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No business", response.data["detail"])
