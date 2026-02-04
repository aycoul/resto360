"""
Serializers for analytics API endpoints.
"""
from rest_framework import serializers


class TrackMenuViewSerializer(serializers.Serializer):
    """Serializer for tracking menu view events."""

    restaurant_slug = serializers.SlugField(
        max_length=200,
        help_text="Slug of the restaurant menu being viewed",
    )
    session_id = serializers.CharField(
        max_length=100,
        help_text="Client-generated session identifier",
    )
    source = serializers.ChoiceField(
        choices=["qr", "link", "whatsapp", "other"],
        default="link",
        help_text="How the menu was accessed",
    )
    user_agent = serializers.CharField(
        max_length=500,
        required=False,
        default="",
        allow_blank=True,
        help_text="Browser/device user agent",
    )


class AnalyticsSummarySerializer(serializers.Serializer):
    """Serializer for analytics summary response."""

    views_today = serializers.IntegerField()
    views_week = serializers.IntegerField()
    views_month = serializers.IntegerField()
    unique_today = serializers.IntegerField()
    menu_items = serializers.IntegerField()
