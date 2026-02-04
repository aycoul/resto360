"""
Analytics service layer for tracking menu views and generating summaries.
"""
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.authentication.models import Restaurant
from apps.menu.models import MenuItem

from .models import DailyMenuStats, MenuView


def track_menu_view(
    restaurant: Restaurant,
    session_id: str,
    source: str = "link",
    user_agent: str = "",
) -> MenuView:
    """
    Record a menu view event.

    Args:
        restaurant: The restaurant whose menu was viewed
        session_id: Client-generated session identifier
        source: How the menu was accessed (qr, link, whatsapp, other)
        user_agent: Browser/device user agent string

    Returns:
        The created MenuView instance
    """
    # Validate source
    valid_sources = [choice[0] for choice in MenuView.SOURCE_CHOICES]
    if source not in valid_sources:
        source = "other"

    return MenuView.all_objects.create(
        restaurant=restaurant,
        session_id=session_id,
        source=source,
        user_agent=user_agent[:500],  # Truncate to field max length
    )


def get_analytics_summary(restaurant: Restaurant) -> dict:
    """
    Get analytics summary for a restaurant.

    Returns view counts for today, this week, and this month,
    plus unique visitors and menu item count.

    Args:
        restaurant: The restaurant to get analytics for

    Returns:
        Dictionary with views_today, views_week, views_month,
        unique_today, and menu_items
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # Base queryset for this restaurant
    views_qs = MenuView.all_objects.filter(restaurant=restaurant)

    # Views today
    views_today = views_qs.filter(viewed_at__gte=today_start).count()

    # Unique visitors today (by session_id)
    unique_today = (
        views_qs.filter(viewed_at__gte=today_start)
        .values("session_id")
        .distinct()
        .count()
    )

    # Views this week
    views_week = views_qs.filter(viewed_at__gte=week_start).count()

    # Views this month
    views_month = views_qs.filter(viewed_at__gte=month_start).count()

    # Menu item count
    menu_items = MenuItem.all_objects.filter(
        restaurant=restaurant, is_available=True
    ).count()

    return {
        "views_today": views_today,
        "views_week": views_week,
        "views_month": views_month,
        "unique_today": unique_today,
        "menu_items": menu_items,
    }


def aggregate_daily_stats(restaurant: Restaurant, date=None) -> DailyMenuStats:
    """
    Aggregate menu view stats for a specific day.

    Creates or updates the DailyMenuStats record for the given date.
    Typically called by a scheduled task at end of day.

    Args:
        restaurant: The restaurant to aggregate stats for
        date: The date to aggregate (defaults to today)

    Returns:
        The created/updated DailyMenuStats instance
    """
    if date is None:
        date = timezone.now().date()

    # Date range for the day
    day_start = timezone.make_aware(
        timezone.datetime.combine(date, timezone.datetime.min.time())
    )
    day_end = day_start + timedelta(days=1)

    # Base queryset
    views_qs = MenuView.all_objects.filter(
        restaurant=restaurant, viewed_at__gte=day_start, viewed_at__lt=day_end
    )

    # Total views
    total_views = views_qs.count()

    # Unique visitors
    unique_visitors = views_qs.values("session_id").distinct().count()

    # QR scans
    qr_scans = views_qs.filter(source="qr").count()

    # Create or update the daily stats
    stats, _ = DailyMenuStats.all_objects.update_or_create(
        restaurant=restaurant,
        date=date,
        defaults={
            "total_views": total_views,
            "unique_visitors": unique_visitors,
            "qr_scans": qr_scans,
            "top_items": [],  # Placeholder for future item-level tracking
        },
    )

    return stats
